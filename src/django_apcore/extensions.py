"""Extension adapter layer for apcore v0.6.0.

Implements apcore protocols (Discoverer, ModuleValidator) with Django-specific
logic, and provides setup_extensions() to build a configured ExtensionManager
from Django settings.
"""

from __future__ import annotations

import contextlib
import importlib
import inspect
import logging
import typing
from pathlib import Path
from typing import TYPE_CHECKING, Any

from apcore import (
    MAX_MODULE_ID_LENGTH,
    RESERVED_WORDS,
    ExtensionManager,
)

if TYPE_CHECKING:
    from django_apcore.settings import ApcoreSettings

logger = logging.getLogger("django_apcore")


class DjangoDiscoverer:
    """Discovers apcore modules from Django project structure.

    Implements the apcore Discoverer protocol.

    Discovery sources (in order):
    1. YAML binding files from APCORE_MODULE_DIR matching APCORE_BINDING_PATTERN
    2. @module-decorated functions from INSTALLED_APPS apcore_modules submodules
    """

    def __init__(self, settings: ApcoreSettings) -> None:
        self._settings = settings

    def discover(self, roots: list[str]) -> list[dict[str, Any]]:
        """Discover modules from Django project structure.

        Args:
            roots: Root directories to search (provided by apcore but
                   supplemented with Django-specific sources).

        Returns:
            List of dicts with at least 'module_id' and 'module' keys.
        """
        discovered: list[dict[str, Any]] = []
        module_dir = Path(self._settings.module_dir)
        if module_dir.exists() and module_dir.is_dir():
            discovered.extend(self._load_bindings(module_dir))
        discovered.extend(self._scan_installed_apps())
        return discovered

    def _load_bindings(self, module_dir: Path) -> list[dict[str, Any]]:
        """Load YAML binding files from the module directory."""
        results: list[dict[str, Any]] = []
        try:
            from apcore import BindingLoader, FunctionModule, Registry

            temp_registry = Registry()
            loader = BindingLoader()
            modules = loader.load_binding_dir(
                str(module_dir),
                temp_registry,
                pattern=self._settings.binding_pattern,
            )
            if modules:
                for fm in modules:
                    fm = self._adapt_view_module(fm, FunctionModule)
                    results.append({"module_id": fm.module_id, "module": fm})
            logger.info(
                "Discovered %d binding modules from %s",
                len(results),
                module_dir,
            )
        except ImportError:
            logger.warning("apcore.BindingLoader not available; skipping binding files")
        except Exception:
            logger.exception("Error loading binding files from %s", module_dir)
        return results

    @staticmethod
    def _adapt_view_module(fm: Any, function_module_cls: type) -> Any:
        """Wrap a Django view function so it can be called via MCP.

        Django view functions (django-ninja, DRF) expect a ``request`` object
        as their first parameter plus typed body/path parameters.  MCP calls
        pass flat keyword arguments.  This method detects view functions and
        creates a thin wrapper that:

        1. Supplies a dummy ``HttpRequest`` for the ``request`` parameter.
        2. Collects kwargs that belong to a Pydantic body model and
           reconstructs it.
        3. Passes remaining kwargs as path/query parameters.
        4. Unwraps ``(status_code, data)`` tuple returns used by django-ninja.
        """
        func = fm._func  # noqa: SLF001
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())

        # Only adapt functions whose first parameter is 'request'
        if not params or params[0] != "request":
            return fm

        # Resolve type hints to find Pydantic body parameters
        hints: dict[str, Any] = {}
        with contextlib.suppress(Exception):
            hints = typing.get_type_hints(func)

        from pydantic import BaseModel

        body_param_name: str | None = None
        body_model_cls: type[BaseModel] | None = None
        for name in params[1:]:
            hint = hints.get(name)
            if (
                hint is not None
                and isinstance(hint, type)
                and issubclass(hint, BaseModel)
            ):
                body_param_name = name
                body_model_cls = hint
                break

        # Capture in closure-safe locals
        orig_func = func
        bpn = body_param_name
        bmc = body_model_cls

        def adapted(**kwargs: Any) -> Any:
            from django.test import RequestFactory

            request = RequestFactory().get("/")

            call_kwargs: dict[str, Any] = {}
            if bmc is not None and bpn is not None:
                body_fields = set(bmc.model_fields.keys())
                body_data = {k: v for k, v in kwargs.items() if k in body_fields}
                non_body = {k: v for k, v in kwargs.items() if k not in body_fields}
                call_kwargs[bpn] = bmc(**body_data)
                call_kwargs.update(non_body)
            else:
                call_kwargs = dict(kwargs)

            result = orig_func(request, **call_kwargs)
            # django-ninja views may return (status_code, data) tuples
            if isinstance(result, tuple) and len(result) == 2:
                return result[1]
            return result

        adapted.__name__ = func.__name__
        adapted.__module__ = func.__module__
        adapted.__doc__ = func.__doc__
        adapted.__annotations__ = {"return": dict}

        return function_module_cls(
            func=adapted,
            module_id=fm.module_id,
            description=fm.description,
            tags=fm.tags,
            version=fm.version,
            input_schema=fm.input_schema,
            output_schema=fm.output_schema,
        )

    def _scan_installed_apps(self) -> list[dict[str, Any]]:
        """Scan INSTALLED_APPS for apcore_modules submodules."""
        results: list[dict[str, Any]] = []
        try:
            from django.apps import apps

            for app_config in apps.get_app_configs():
                module_name = f"{app_config.name}.apcore_modules"
                try:
                    module = importlib.import_module(module_name)
                    for attr_name in dir(module):
                        obj = getattr(module, attr_name)
                        if callable(obj) and hasattr(obj, "apcore_module"):
                            fm = obj.apcore_module
                            results.append({"module_id": fm.module_id, "module": fm})
                except ImportError:
                    continue
                except Exception:
                    logger.warning("Error scanning %s", module_name, exc_info=True)
        except Exception:
            logger.warning("Error scanning installed apps", exc_info=True)
        return results


class DjangoModuleValidator:
    """Validates modules against Django-specific rules.

    Implements the apcore ModuleValidator protocol.

    Checks:
    - module_id attribute exists
    - module_id does not contain reserved words
    - module_id does not exceed MAX_MODULE_ID_LENGTH
    - Delegates to any extra validators
    """

    def __init__(self, extra_validators: list[Any] | None = None) -> None:
        self._extra = extra_validators or []

    def validate(self, module: Any) -> list[str]:
        """Validate a module against Django-specific rules.

        Args:
            module: The module object to validate. Expected to have a
                    ``module_id`` attribute.

        Returns:
            List of error strings. Empty list means valid.
        """
        errors: list[str] = []
        module_id = getattr(module, "module_id", None)
        if module_id is None:
            errors.append("Module has no module_id attribute")
            return errors

        # Check reserved words
        parts = module_id.split(".")
        for part in parts:
            if part in RESERVED_WORDS:
                errors.append(
                    f"Module ID '{module_id}' contains reserved word '{part}'"
                )

        # Check length
        if len(module_id) > MAX_MODULE_ID_LENGTH:
            errors.append(
                f"Module ID '{module_id}' exceeds max length "
                f"({len(module_id)} > {MAX_MODULE_ID_LENGTH})"
            )

        # Delegate to extra validators
        for validator in self._extra:
            try:
                extra_errors = validator.validate(module)
                errors.extend(extra_errors)
            except Exception:
                logger.warning(
                    "Extra validator %s raised an error",
                    type(validator).__name__,
                    exc_info=True,
                )

        return errors


def setup_extensions(settings: ApcoreSettings) -> ExtensionManager:
    """Build and configure an ExtensionManager from Django settings.

    Registers the following extension points:
    - ``discoverer``: A DjangoDiscoverer instance
    - ``module_validator``: A DjangoModuleValidator instance
    - ``middleware``: Any middleware classes from settings.middlewares
    - ``acl``: An ACL loaded from settings.acl_path (if set)
    - ``span_exporter``: A span exporter based on settings.tracing (if set)

    Args:
        settings: Validated ApcoreSettings dataclass.

    Returns:
        A fully configured ExtensionManager.
    """
    ext_mgr = ExtensionManager()

    # Discoverer
    ext_mgr.register("discoverer", DjangoDiscoverer(settings))

    # Module validator
    extra_validators = _resolve_extra_validators(settings.module_validators)
    ext_mgr.register("module_validator", DjangoModuleValidator(extra_validators))

    # Middlewares
    for mw_path in settings.middlewares:
        mw = _import_and_instantiate(mw_path)
        if mw is not None:
            ext_mgr.register("middleware", mw)

    # ACL
    if settings.acl_path:
        try:
            from apcore import ACL

            acl = ACL.load(settings.acl_path)
            ext_mgr.register("acl", acl)
        except Exception:
            logger.exception("Failed to load ACL from %s", settings.acl_path)

    # Span exporter
    if settings.tracing:
        exporter = _build_span_exporter(settings.tracing)
        if exporter is not None:
            ext_mgr.register("span_exporter", exporter)

    return ext_mgr


def _resolve_extra_validators(paths: list[str]) -> list[Any]:
    """Import and instantiate extra module validator classes.

    Args:
        paths: List of dotted paths to validator classes.

    Returns:
        List of instantiated validator objects (skipping any that fail).
    """
    validators = []
    for path in paths:
        v = _import_and_instantiate(path)
        if v is not None:
            validators.append(v)
    return validators


def _import_and_instantiate(dotted_path: str) -> Any | None:
    """Import a class by dotted path and instantiate it with no arguments.

    Args:
        dotted_path: Fully-qualified dotted path, e.g. ``myapp.middleware.MyMW``.

    Returns:
        An instance of the class, or None if import/instantiation fails.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        return cls()
    except Exception:
        logger.warning("Failed to import %s", dotted_path, exc_info=True)
        return None


def _build_span_exporter(config: bool | dict) -> Any | None:
    """Build a span exporter from tracing configuration.

    Args:
        config: Either ``True`` (for stdout), or a dict with
                ``exporter`` key specifying the type.

    Returns:
        A SpanExporter instance, or None if unavailable.
    """
    try:
        if config is True:
            from apcore import StdoutExporter

            return StdoutExporter()
        if isinstance(config, dict):
            exporter_name = config.get("exporter", "stdout")
            if exporter_name == "stdout":
                from apcore import StdoutExporter

                return StdoutExporter()
            if exporter_name == "in_memory":
                from apcore import InMemoryExporter

                return InMemoryExporter()
            if exporter_name == "otlp":
                from apcore import OTLPExporter

                kwargs: dict[str, Any] = {}
                if "otlp_endpoint" in config:
                    kwargs["endpoint"] = config["otlp_endpoint"]
                if "otlp_service_name" in config:
                    kwargs["service_name"] = config["otlp_service_name"]
                return OTLPExporter(**kwargs)
    except ImportError:
        logger.warning("Tracing exporter not available; skipping")
    except Exception:
        logger.exception("Failed to build span exporter")
    return None

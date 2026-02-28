"""NinjaScanner: scans django-ninja API instances for endpoint metadata.

Requires django-ninja >= 1.0 (optional dependency).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from django_apcore.scanners.base import BaseScanner, ScannedModule

logger = logging.getLogger("django_apcore")


class NinjaScanner(BaseScanner):
    """Scanner for django-ninja API endpoints.

    Discovers NinjaAPI instances from Django URL patterns, extracts
    Pydantic input/output schemas, and produces ScannedModule instances.
    """

    def get_source_name(self) -> str:
        return "django-ninja"

    def scan(
        self,
        include: str | None = None,
        exclude: str | None = None,
    ) -> list[ScannedModule]:
        """Scan all django-ninja endpoints.

        Args:
            include: Regex pattern to include (matches against module_id).
            exclude: Regex pattern to exclude.

        Returns:
            List of ScannedModule instances.

        Raises:
            ImportError: If django-ninja is not installed.
        """
        self._check_ninja_installed()
        modules = self._scan_all_endpoints()
        return self.filter_modules(modules, include, exclude)

    def _check_ninja_installed(self) -> None:
        """Verify django-ninja is available."""
        try:
            import ninja  # noqa: F401
        except ImportError:
            raise ImportError(
                "django-ninja is required for --source ninja. "
                "Install with: pip install django-apcore[ninja]"
            ) from None

    def _discover_ninja_apis(self) -> list[Any]:
        """Discover all NinjaAPI instances from Django URL patterns."""
        from django.urls import get_resolver

        apis: list[Any] = []
        try:
            from ninja import NinjaAPI

            resolver = get_resolver()
            self._find_apis(resolver.url_patterns, apis, NinjaAPI)
        except ImportError:
            pass
        return apis

    def _find_apis(self, patterns: Any, apis: list[Any], api_class: type) -> None:
        """Recursively search URL patterns for NinjaAPI instances."""
        import functools

        for pattern in patterns:
            cb = getattr(pattern, "callback", None)
            if cb is not None:
                # Direct attribute: callback.api (older django-ninja versions)
                api = getattr(cb, "api", None)
                # functools.partial keyword: django-ninja wraps internal
                # views (openapi_json, default_home) as partial(fn, api=...)
                if api is None and isinstance(cb, functools.partial):
                    api = cb.keywords.get("api")
                if isinstance(api, api_class) and api not in apis:
                    apis.append(api)
            if hasattr(pattern, "url_patterns"):
                self._find_apis(pattern.url_patterns, apis, api_class)

    def _scan_all_endpoints(self) -> list[ScannedModule]:
        """Scan all discovered NinjaAPI instances."""
        apis = self._discover_ninja_apis()
        modules: list[ScannedModule] = []

        for api in apis:
            # OpenAPI paths already contain the full route (e.g. /api/tasks),
            # so we don't need urls_namespace as an additional prefix.
            api_prefix = ""
            func_map = self._build_view_func_map(api)
            try:
                schema = api.get_openapi_schema()
                paths = schema.get("paths", {})

                for path, methods in paths.items():
                    for method, operation in methods.items():
                        if method.lower() in (
                            "get",
                            "post",
                            "put",
                            "patch",
                            "delete",
                        ):
                            module = self._operation_to_module(
                                api,
                                api_prefix,
                                path,
                                method,
                                operation,
                                func_map,
                                schema,
                            )
                            if module:
                                modules.append(module)
            except Exception:
                logger.warning("Error scanning NinjaAPI instance", exc_info=True)

        # Deduplicate IDs
        if modules:
            deduped_ids = self._deduplicate_ids([m.module_id for m in modules])
            for i, module in enumerate(modules):
                if module.module_id != deduped_ids[i]:
                    modules[i] = ScannedModule(
                        module_id=deduped_ids[i],
                        description=module.description,
                        input_schema=module.input_schema,
                        output_schema=module.output_schema,
                        tags=module.tags,
                        target=module.target,
                        version=module.version,
                        warnings=[
                            *module.warnings,
                            f"Module ID renamed from '{module.module_id}' "
                            f"to '{deduped_ids[i]}' to avoid collision",
                        ],
                    )

        return modules

    def _build_view_func_map(self, api: Any) -> dict[str, tuple[str, str]]:
        """Build a mapping from operationId to (module_path, func_name).

        Traverses NinjaAPI's internal routing structures to find the actual
        view function for each operation, so that the generated ``target``
        field uses the correct Python module and function name.

        In django-ninja >= 1.5, ``op.operation_id`` is ``None`` unless the
        user explicitly sets it — the operationId is only auto-generated
        in the OpenAPI schema output.  To handle this, we also index by
        ``func.__name__`` so the fallback lookup in
        ``_operation_to_module`` can match by suffix.
        """
        func_map: dict[str, tuple[str, str]] = {}
        try:
            for _prefix, router in api._routers:
                for path_view in router.path_operations.values():
                    for op in path_view.operations:
                        func = op.view_func
                        if func is None:
                            continue
                        info = (func.__module__, func.__name__)
                        op_id = getattr(op, "operation_id", None)
                        if op_id:
                            func_map[op_id] = info
                        # Always index by func name for fallback lookup
                        func_map[func.__name__] = info
        except Exception:
            logger.debug(
                "Could not build view function map from NinjaAPI internals",
                exc_info=True,
            )
        return func_map

    def _operation_to_module(
        self,
        api: Any,
        api_prefix: str,
        path: str,
        method: str,
        operation: dict[str, Any],
        func_map: dict[str, tuple[str, str]],
        openapi_doc: dict[str, Any] | None = None,
    ) -> ScannedModule | None:
        """Convert an OpenAPI operation to a ScannedModule."""
        try:
            operation_id = operation.get("operationId")
            module_id = self._generate_module_id(
                api_prefix,
                path,
                method,
                operation_id,
            )
            if not operation_id:
                operation_id = module_id

            description = self._extract_description(
                description=operation.get("description"),
                docstring=operation.get("summary"),
                operation_id=operation_id,
            )

            input_schema = self._extract_input_schema(operation, openapi_doc)
            output_schema = self._extract_output_schema(operation, openapi_doc)

            tags = operation.get("tags", [])

            # Resolve target from actual view function when available.
            # Try exact operationId first, then suffix match (django-ninja
            # generates operationId as "{prefix}_{func_name}" in the
            # OpenAPI schema but may leave op.operation_id as None).
            func_info = func_map.get(operation_id)
            if not func_info:
                for name, info in func_map.items():
                    if operation_id.endswith(f"_{name}"):
                        func_info = info
                        break
            if func_info:
                target = f"{func_info[0]}:{func_info[1]}"
            else:
                target = f"{api.__module__}:{operation_id}"

            warnings: list[str] = []
            if not operation.get("description") and not operation.get("summary"):
                warnings.append(
                    f"Endpoint '{method.upper()} {path}' has no description"
                )

            return ScannedModule(
                module_id=module_id,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                tags=tags,
                target=target,
                warnings=warnings,
            )
        except Exception:
            logger.warning(
                "Failed to scan endpoint %s %s",
                method.upper(),
                path,
                exc_info=True,
            )
            return None

    def _generate_module_id(
        self,
        api_prefix: str,
        path: str,
        method: str,
        operation_id: str | None = None,
    ) -> str:
        """Generate module ID per BL-001.

        Format: {api_prefix}.{path_segments}.{action} lowercased,
        special chars replaced.

        When *operation_id* is available (e.g. ``list_tasks``), the action
        verb is extracted from it (``list``) instead of the raw HTTP method,
        producing more semantic IDs like ``api.tasks.list`` instead of
        ``api.tasks.get``.
        """
        # Clean prefix and path
        combined = f"{api_prefix}/{path}".strip("/")
        # Remove path parameters (e.g., {id})
        combined = re.sub(r"\{[^}]+\}", "", combined)
        # Replace non-alphanumeric with dots
        combined = re.sub(r"[^a-zA-Z0-9]+", ".", combined)
        # Remove trailing/leading dots
        combined = combined.strip(".")
        # Derive action: prefer first segment of operationId over HTTP method
        action = method
        if operation_id:
            parts = operation_id.split("_")
            if parts[0]:
                action = parts[0]
        # Append action
        module_id = f"{combined}.{action}".lower()
        # Clean up double dots
        module_id = re.sub(r"\.+", ".", module_id)
        return module_id

    def _extract_description(
        self,
        description: str | None,
        docstring: str | None,
        operation_id: str,
    ) -> str:
        """Extract description per BL-004 priority chain."""
        if description:
            return description
        if docstring:
            return docstring.split("\n")[0].strip()
        return f"No description available for {operation_id}"

    # _extract_input_schema, _extract_output_schema, and _deduplicate_ids
    # are inherited from BaseScanner.

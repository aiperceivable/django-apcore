"""Django AppConfig for django-apcore.

Provides auto-discovery of YAML binding files and @module-decorated functions
across all installed Django apps during startup.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from django.apps import AppConfig, apps

if TYPE_CHECKING:
    from apcore import Registry

logger = logging.getLogger("django_apcore")


class ApcoreAppConfig(AppConfig):
    """Django AppConfig for django-apcore."""

    name = "django_apcore"
    verbose_name = "Django apcore"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Initialize apcore on Django startup.

        1. Validate APCORE_* settings
        2. If APCORE_AUTO_DISCOVER is True:
           a. Load YAML binding files from APCORE_MODULE_DIR
           b. Scan INSTALLED_APPS for @module-decorated functions
        """
        from django_apcore.registry import get_registry
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()

        if not settings.auto_discover:
            logger.debug("Auto-discovery disabled (APCORE_AUTO_DISCOVER=False)")
            return

        registry = get_registry()
        self._register_event_listeners(registry)

        # Load YAML binding files
        module_dir = Path(settings.module_dir)
        if module_dir.exists() and module_dir.is_dir():
            self._load_bindings(registry, module_dir, settings.binding_pattern)
        else:
            logger.warning(
                "Module directory not found: %s. "
                "Skipping auto-discovery of binding files.",
                module_dir,
            )

        # Scan INSTALLED_APPS for @module-decorated functions
        self._scan_apps_for_modules(registry)

        logger.info("Auto-discovery complete")

        # Start embedded MCP server if configured
        if settings.embedded_server:
            from django_apcore.registry import start_embedded_server

            try:
                start_embedded_server()
            except Exception:
                logger.warning(
                    "Failed to start embedded MCP server",
                    exc_info=True,
                )

    def _register_event_listeners(self, registry: Registry) -> None:
        """Register event listeners on the registry for debug logging.

        Gracefully handles cases where the registry does not support events.
        """
        try:
            registry.on(
                "register",
                lambda module_id, module: logger.debug(
                    "Registry event: registered module '%s'",
                    module_id,
                ),
            )
            logger.debug("Registered event listeners on registry")
        except (AttributeError, TypeError):
            logger.debug(
                "Registry does not support events; "
                "skipping event listener registration"
            )

    def _load_bindings(
        self, registry: Registry, module_dir: Path, pattern: str
    ) -> None:
        """Load YAML binding files from the module directory."""
        try:
            from apcore import BindingLoader

            loader = BindingLoader()
            modules = loader.load_binding_dir(
                str(module_dir), registry, pattern=pattern
            )
            count = len(modules) if modules else 0
            logger.info("Loaded %d binding modules from %s", count, module_dir)
        except ImportError:
            logger.warning(
                "apcore.BindingLoader not available; " "skipping binding file loading"
            )
        except Exception:
            logger.exception("Error loading binding files from %s", module_dir)

    def _scan_apps_for_modules(self, registry: Registry) -> None:
        """Scan INSTALLED_APPS for apcore_modules submodules."""
        for app_config in apps.get_app_configs():
            module_name = f"{app_config.name}.apcore_modules"
            try:
                module = importlib.import_module(module_name)
                # Scan module for functions with .apcore_module attribute
                for attr_name in dir(module):
                    obj = getattr(module, attr_name)
                    if callable(obj) and hasattr(obj, "apcore_module"):
                        try:
                            fm = obj.apcore_module
                            registry.register(fm.module_id, fm)
                            logger.debug(
                                "Registered @module function: %s.%s",
                                module_name,
                                attr_name,
                            )
                        except Exception:
                            logger.warning(
                                "Failed to register module from %s.%s",
                                module_name,
                                attr_name,
                                exc_info=True,
                            )
            except ImportError:
                # App does not have an apcore_modules submodule -- that's fine
                continue
            except Exception:
                logger.warning(
                    "Error scanning %s for apcore modules",
                    module_name,
                    exc_info=True,
                )

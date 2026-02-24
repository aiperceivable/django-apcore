"""Django AppConfig for django-apcore (Extension-First architecture)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.apps import AppConfig

if TYPE_CHECKING:
    from apcore import Registry

logger = logging.getLogger("django_apcore")


class ApcoreAppConfig(AppConfig):
    """Django AppConfig for django-apcore."""

    name = "django_apcore"
    verbose_name = "Django apcore"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Initialize apcore on Django startup (Extension-First flow).

        1. Validate APCORE_* settings
        2. Build ExtensionManager via setup_extensions()
        3. Create Registry + Executor, apply extensions
        4. Auto-discover modules via registry.discover()
        5. Optionally set up hot-reload watching
        6. Optionally start embedded MCP server
        """
        from django_apcore.registry import get_executor, get_registry
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()

        if not settings.auto_discover:
            logger.debug("Auto-discovery disabled (APCORE_AUTO_DISCOVER=False)")
            return

        registry = get_registry()
        self._register_event_listeners(registry)

        # Trigger ExtensionManager assembly (discoverer, validator, middlewares, etc.)
        get_executor()

        # Discover modules via DjangoDiscoverer
        count = registry.discover()
        logger.info("Auto-discovery complete: %d modules registered", count)

        # Explorer
        if settings.explorer_enabled:
            self._register_explorer_urls(
                settings.explorer_url_prefix,
                settings.explorer_allow_execute,
            )

        # Hot-reload
        if settings.hot_reload:
            try:
                registry.watch()
                logger.info("Hot-reload watching enabled")
            except ImportError:
                logger.warning(
                    "Hot-reload requires 'watchdog' package. "
                    "Install with: pip install watchdog"
                )
            except Exception:
                logger.warning("Failed to enable hot-reload", exc_info=True)

        # Embedded MCP server
        if settings.embedded_server:
            from django_apcore.registry import start_embedded_server

            try:
                start_embedded_server()
            except Exception:
                logger.warning(
                    "Failed to start embedded MCP server",
                    exc_info=True,
                )

    def _register_explorer_urls(
        self, url_prefix: str, allow_execute: bool
    ) -> None:
        """Dynamically add explorer URL patterns to the root URLconf."""
        from importlib import import_module

        from django.conf import settings as django_settings
        from django.urls import include, path

        from django_apcore.urls import explorer_urlpatterns

        # Normalize prefix: strip leading/trailing slashes
        prefix = url_prefix.strip("/")
        if prefix:
            prefix += "/"

        try:
            urlconf_module = import_module(django_settings.ROOT_URLCONF)
            urlconf_module.urlpatterns.append(
                path(prefix, include((explorer_urlpatterns, "apcore_explorer")))
            )
            logger.info(
                "Explorer enabled at /%s (execute=%s)",
                prefix,
                "on" if allow_execute else "off",
            )
        except Exception:
            logger.warning(
                "Failed to register explorer URLs at /%s",
                prefix,
                exc_info=True,
            )

    def _register_event_listeners(self, registry: Registry) -> None:
        """Register event listeners on the registry for debug logging."""
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

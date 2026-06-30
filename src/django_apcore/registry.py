"""Singleton apcore.Registry and Executor wrappers for Django.

Provides process-level singletons for Registry, ExtensionManager, and
Executor, all lazily created on first access. Thread-safe via module-level
locks protecting singleton creation.

The ExtensionManager (created by ``setup_extensions()``) replaces the
previous manual middleware/ACL/tracing resolution. ``get_executor()`` now
delegates assembly to ``ExtensionManager.apply()``.
"""

from __future__ import annotations

import contextlib
import importlib
import logging
import threading
from typing import Any

from apcore import Registry

logger = logging.getLogger("django_apcore")

_registry: Registry | None = None
_lock = threading.Lock()

_ext_manager: Any = None
_ext_manager_lock = threading.Lock()

_executor: Any = None
_executor_lock = threading.Lock()

_context_factory: Any = None
_context_factory_lock = threading.Lock()

_metrics_collector: Any = None
_metrics_collector_lock = threading.Lock()

_embedded_server: Any = None
_embedded_server_lock = threading.Lock()


def get_registry() -> Registry:
    """Return the singleton apcore Registry for this Django process.

    The registry is lazily created on first call. It is populated by
    ApcoreAppConfig.ready() auto-discovery if APCORE_AUTO_DISCOVER is True.

    Returns:
        The shared apcore.Registry instance.
    """
    global _registry
    if _registry is None:
        with _lock:
            if _registry is None:
                logger.debug("Creating new apcore.Registry instance")
                _registry = Registry()
    return _registry


def get_extension_manager() -> Any:
    """Return the singleton ExtensionManager for this Django process.

    The extension manager is lazily created on first call via
    ``setup_extensions()`` from ``django_apcore.extensions``.

    Returns:
        The shared apcore.ExtensionManager instance.
    """
    global _ext_manager
    if _ext_manager is None:
        with _ext_manager_lock:
            if _ext_manager is None:
                from django_apcore.extensions import setup_extensions
                from django_apcore.settings import get_apcore_settings

                settings = get_apcore_settings()
                _ext_manager = setup_extensions(settings)
                logger.debug("Created ExtensionManager via setup_extensions()")
    return _ext_manager


def get_executor() -> Any:
    """Return the singleton apcore Executor for this Django process.

    The executor is lazily created on first call. Assembly of middlewares,
    ACL, and span exporters is delegated to the ExtensionManager via
    ``ext_mgr.apply(registry, executor)``.

    Returns:
        The shared apcore.Executor instance.
    """
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:
                from apcore import Executor

                from django_apcore.settings import get_apcore_settings

                settings = get_apcore_settings()
                registry = get_registry()
                config = _resolve_config(settings.executor_config)

                _executor = Executor(registry, config=config)

                # Let ExtensionManager wire middlewares, ACL, span exporters
                ext_mgr = get_extension_manager()
                ext_mgr.apply(registry, _executor)

                logger.debug("Created apcore.Executor with ExtensionManager assembly")
    return _executor


def _resolve_dotted_callable(dotted_path: str | None) -> Any | None:
    """Resolve a dotted path (e.g. ``apcore_toolkit.to_markdown``) to an object.

    Returns None if the path is empty or cannot be imported/resolved. Mirrors
    the resolver used by the ``apcore_serve`` command so the embedded server
    interprets ``APCORE_OUTPUT_FORMATTER`` identically.
    """
    if not dotted_path:
        return None
    module_path, sep, attr_name = dotted_path.rpartition(".")
    if not sep or not module_path:
        return None
    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, attr_name)
    except (ImportError, AttributeError):
        return None


def _resolve_config(data: dict[str, Any] | None) -> Any:
    """Create an Executor Config from a dict.

    Args:
        data: Config dict, or None.

    Returns:
        Config instance or None.
    """
    if data is None:
        return None
    from apcore import Config

    return Config(data=data)


def get_metrics_collector() -> Any | None:
    """Return the singleton MetricsCollector, or None if metrics disabled.

    Returns:
        MetricsCollector instance or None.
    """
    global _metrics_collector
    if _metrics_collector is None:
        with _metrics_collector_lock:
            if _metrics_collector is None:
                from django_apcore.settings import get_apcore_settings

                settings = get_apcore_settings()
                if not settings.metrics:
                    return None
                _metrics_collector = _create_metrics_collector(settings.metrics)
    return _metrics_collector


def _create_metrics_collector(config: bool | dict[str, Any]) -> Any:
    """Create a MetricsCollector from settings.

    Args:
        config: True for defaults, or a dict with buckets.

    Returns:
        A MetricsCollector instance.
    """
    from apcore.observability.metrics import MetricsCollector

    if config is True:
        return MetricsCollector()

    assert isinstance(config, dict)
    kwargs: dict[str, Any] = {}
    if "buckets" in config:
        kwargs["buckets"] = config["buckets"]
    return MetricsCollector(**kwargs)


def _reset_metrics_collector() -> None:
    """Reset the singleton metrics collector. For testing only."""
    global _metrics_collector
    with _metrics_collector_lock:
        _metrics_collector = None


def start_embedded_server() -> Any | None:
    """Start the embedded MCP server if configured.

    Creates an MCPServer, calls ``.start()``, and returns the instance.
    Returns None if ``APCORE_EMBEDDED_SERVER`` is not configured or
    apcore-mcp is not installed.
    """
    global _embedded_server
    if _embedded_server is not None:
        return _embedded_server
    with _embedded_server_lock:
        if _embedded_server is not None:
            return _embedded_server

        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        if not settings.embedded_server:
            return None

        try:
            from apcore_mcp import MCPServer
        except ImportError:
            logger.warning(
                "apcore-mcp is not installed; "
                "cannot start embedded MCP server. "
                "Install with: pip install django-apcore[mcp]"
            )
            return None

        # Resolve config
        config = (
            settings.embedded_server
            if isinstance(settings.embedded_server, dict)
            else {}
        )
        transport = config.get("transport", settings.serve_transport)
        host = config.get("host", settings.serve_host)
        port = config.get("port", settings.serve_port)
        name = config.get("name", settings.server_name)
        version = config.get("version", settings.server_version)

        # Auto-detect executor vs registry
        use_executor = (
            settings.middlewares
            or settings.acl_path
            or settings.executor_config
            or settings.observability_logging
            or settings.tracing
            or settings.metrics
        )

        registry_or_executor = get_executor() if use_executor else get_registry()

        kwargs: dict[str, Any] = {
            "transport": transport,
            "host": host,
            "port": port,
            "name": name,
        }
        if version is not None:
            kwargs["version"] = version

        metrics_collector = get_metrics_collector()
        if metrics_collector is not None:
            kwargs["metrics_collector"] = metrics_collector
        if settings.serve_validate_inputs or settings.validate_inputs:
            kwargs["validate_inputs"] = True
        if settings.serve_tags:
            kwargs["tags"] = settings.serve_tags
        if settings.serve_prefix:
            kwargs["prefix"] = settings.serve_prefix

        # Async task bridge (apcore-mcp 0.14.0+): size the in-process task
        # manager from the same APCORE_TASK_* settings used by AsyncTaskManager.
        kwargs["async_max_concurrent"] = settings.task_max_concurrent
        kwargs["async_max_tasks"] = settings.task_max_tasks

        # JWT authentication (apcore-mcp 0.7.0+).
        # MCPServer defaults ``require_auth=True`` (apcore-mcp 0.14.0+), so we
        # must opt out explicitly when no authenticator is configured —
        # otherwise the embedded server would reject every request.
        authenticator = None
        if settings.jwt_secret is not None:
            try:
                from apcore_mcp.auth import JWTAuthenticator

                authenticator = JWTAuthenticator(
                    settings.jwt_secret,
                    algorithms=[settings.jwt_algorithm],
                    audience=settings.jwt_audience,
                    issuer=settings.jwt_issuer,
                )
            except ImportError:
                logger.warning(
                    "apcore-mcp >= 0.7.0 is required for JWT authentication; "
                    "APCORE_JWT_SECRET will be ignored"
                )
        if authenticator is not None:
            kwargs["authenticator"] = authenticator
            kwargs["require_auth"] = True
        else:
            kwargs["require_auth"] = False

        # Pipeline / output features. apcore-mcp 0.17.0+ gives the non-blocking
        # ``MCPServer`` full parity with the blocking ``serve()`` path, so the
        # embedded server can now use output formatting, pipeline strategy,
        # observability, redaction and tracing — previously these were only
        # available via ``manage.py apcore_serve``.
        output_formatter = _resolve_dotted_callable(settings.output_formatter)
        if settings.output_formatter and output_formatter is None:
            logger.warning(
                "Could not resolve APCORE_OUTPUT_FORMATTER '%s'; the embedded "
                "MCP server will emit raw JSON.",
                settings.output_formatter,
            )
        if output_formatter is not None:
            kwargs["output_formatter"] = output_formatter
        if settings.serve_output_format is not None:
            kwargs["output_format"] = settings.serve_output_format
        if settings.serve_strategy is not None:
            kwargs["strategy"] = settings.serve_strategy
        if settings.serve_observability:
            kwargs["observability"] = True
        # ``redact_output`` defaults to True in MCPServer; only override to
        # disable it (APCORE_SERVE_REDACT_OUTPUT = False).
        if settings.serve_redact_output is False:
            kwargs["redact_output"] = False
        if settings.serve_trace:
            kwargs["trace"] = True

        # Explorer UI (apcore-mcp 0.17.0+ on MCPServer). Only meaningful for
        # HTTP transports; MCPServer ignores it for stdio.
        if settings.explorer_enabled:
            kwargs["explorer"] = True
            kwargs["explorer_prefix"] = settings.explorer_prefix
            if settings.explorer_allow_execute:
                kwargs["allow_execute"] = True
            if settings.explorer_title is not None:
                kwargs["explorer_title"] = settings.explorer_title
            if settings.explorer_project_name is not None:
                kwargs["explorer_project_name"] = settings.explorer_project_name
            if settings.explorer_project_url is not None:
                kwargs["explorer_project_url"] = settings.explorer_project_url

        server = MCPServer(registry_or_executor, **kwargs)
        server.start()
        _embedded_server = server
        logger.info(
            "Embedded MCP server started (%s on %s:%d)",
            transport,
            host,
            port,
        )
        return _embedded_server


def stop_embedded_server() -> None:
    """Stop the embedded MCP server if running."""
    global _embedded_server
    with _embedded_server_lock:
        if _embedded_server is not None:
            try:
                _embedded_server.stop()
            except Exception:
                logger.warning(
                    "Error stopping embedded MCP server",
                    exc_info=True,
                )
            _embedded_server = None


def _reset_embedded_server() -> None:
    """Reset the embedded server singleton. For testing only."""
    global _embedded_server
    with _embedded_server_lock:
        if _embedded_server is not None:
            with contextlib.suppress(Exception):
                _embedded_server.stop()
        _embedded_server = None


def get_context_factory() -> Any:
    """Return the singleton ContextFactory for this Django process.

    Resolves the factory from ``APCORE_CONTEXT_FACTORY`` setting.  When the
    setting is *not* configured, the built-in ``DjangoContextFactory`` is
    returned so that Django views calling ``Executor.call()`` directly always
    get a properly populated ``Context`` with the current user's identity.

    Usage from a Django view::

        from django_apcore.registry import get_context_factory, get_executor

        factory = get_context_factory()
        ctx = factory.create_context(request)
        result = get_executor().call("my.module", inputs, context=ctx)

    Returns:
        An object implementing the ``ContextFactory`` protocol
        (``create_context(request) -> Context``).
    """
    global _context_factory
    if _context_factory is None:
        with _context_factory_lock:
            if _context_factory is None:
                from django_apcore.settings import get_apcore_settings

                settings = get_apcore_settings()
                if settings.context_factory is not None:
                    module_path, class_name = settings.context_factory.rsplit(".", 1)
                    mod = importlib.import_module(module_path)
                    cls = getattr(mod, class_name)
                    _context_factory = cls()
                else:
                    from django_apcore.context import (
                        DjangoContextFactory,
                    )

                    _context_factory = DjangoContextFactory()
                logger.debug(
                    "Created ContextFactory: %s",
                    type(_context_factory).__name__,
                )
    return _context_factory


def _reset_context_factory() -> None:
    """Reset the singleton context factory. For testing only."""
    global _context_factory
    with _context_factory_lock:
        _context_factory = None


def _reset_executor() -> None:
    """Reset the singleton executor. For testing only."""
    global _executor
    with _executor_lock:
        _executor = None


def _reset_extension_manager() -> None:
    """Reset the singleton extension manager. For testing only."""
    global _ext_manager
    with _ext_manager_lock:
        _ext_manager = None


def _reset_registry() -> None:
    """Reset the singleton registry. For testing only.

    This causes the next call to get_registry() to create a fresh
    Registry instance. Also resets the extension manager, executor,
    and context factory since they depend on the registry.
    """
    global _registry
    with _lock:
        _registry = None
    _reset_extension_manager()
    _reset_executor()
    _reset_context_factory()
    _reset_metrics_collector()
    _reset_embedded_server()

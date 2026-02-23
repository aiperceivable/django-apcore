"""Singleton apcore.Registry and Executor wrappers for Django.

Provides process-level singletons for Registry and Executor, both lazily
created on first access. Thread-safe via module-level locks protecting
singleton creation.
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

_executor: Any = None
_executor_lock = threading.Lock()

_context_factory: Any = None
_context_factory_lock = threading.Lock()

_metrics_collector: Any = None
_metrics_collector_lock = threading.Lock()

_embedded_server: Any = None
_embedded_server_lock = threading.Lock()

_tracing_exporter: Any = None


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


def get_executor() -> Any:
    """Return the singleton apcore Executor for this Django process.

    The executor is lazily created on first call, configured from
    APCORE_* settings (middlewares, ACL, executor_config, observability).

    Returns:
        The shared apcore.Executor instance.
    """
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:
                from django_apcore.settings import get_apcore_settings

                settings = get_apcore_settings()
                registry = get_registry()

                middlewares = _resolve_middlewares(settings.middlewares)

                if settings.observability_logging:
                    obs_mw = _resolve_obs_logging_middleware(
                        settings.observability_logging
                    )
                    middlewares.insert(0, obs_mw)

                if settings.tracing:
                    tracing_mw = _resolve_tracing_middleware(settings.tracing)
                    middlewares.insert(0, tracing_mw)

                if settings.metrics:
                    collector = get_metrics_collector()
                    if collector is not None:
                        from apcore.observability.metrics import (
                            MetricsMiddleware,
                        )

                        middlewares.insert(0, MetricsMiddleware(collector=collector))

                acl = _resolve_acl(settings.acl_path)
                config = _resolve_config(settings.executor_config)

                from apcore import Executor

                _executor = Executor(
                    registry,
                    middlewares=middlewares,
                    acl=acl,
                    config=config,
                )
                logger.debug(
                    "Created apcore.Executor with %d middlewares",
                    len(middlewares),
                )
    return _executor


def _resolve_middlewares(paths: list[str]) -> list[Any]:
    """Import and instantiate middleware classes from dotted paths.

    Args:
        paths: List of dotted path strings (e.g., 'myapp.middleware.LoggingMiddleware').

    Returns:
        List of instantiated middleware objects.
    """
    middlewares = []
    for path in paths:
        module_path, class_name = path.rsplit(".", 1)
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        middlewares.append(cls())
    return middlewares


def _resolve_acl(path: str | None) -> Any:
    """Load ACL from a YAML file path.

    Args:
        path: File path to ACL YAML, or None.

    Returns:
        ACL instance or None.
    """
    if path is None:
        return None
    from apcore import ACL

    return ACL.load(path)


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


def _resolve_obs_logging_middleware(
    config: bool | dict,
) -> Any:
    """Create an ObsLoggingMiddleware from settings.

    Args:
        config: True for defaults, or a dict with log_inputs,
            log_outputs, level, format, redact_sensitive options.

    Returns:
        An ObsLoggingMiddleware instance.
    """
    from apcore import ObsLoggingMiddleware

    if config is True:
        return ObsLoggingMiddleware()

    kwargs: dict[str, Any] = {}
    if "log_inputs" in config:
        kwargs["log_inputs"] = config["log_inputs"]
    if "log_outputs" in config:
        kwargs["log_outputs"] = config["log_outputs"]

    # Create a ContextLogger if any logger options are specified
    logger_keys = {"level", "format", "redact_sensitive"}
    if logger_keys & config.keys():
        from apcore import ContextLogger

        logger_kwargs: dict[str, Any] = {
            "name": "apcore.obs_logging",
        }
        if "level" in config:
            logger_kwargs["level"] = config["level"]
        if "format" in config:
            logger_kwargs["format"] = config["format"]
        if "redact_sensitive" in config:
            logger_kwargs["redact_sensitive"] = config["redact_sensitive"]
        kwargs["logger"] = ContextLogger(**logger_kwargs)

    return ObsLoggingMiddleware(**kwargs)


def _resolve_tracing_middleware(config: bool | dict) -> Any:
    """Create a TracingMiddleware from settings.

    Also stores the exporter in ``_tracing_exporter`` so it can be
    shut down on reset (important for OTLPExporter which flushes spans).

    Args:
        config: True for defaults, or a dict with exporter/sampling options.

    Returns:
        A TracingMiddleware instance.
    """
    global _tracing_exporter
    from apcore.observability.tracing import TracingMiddleware

    if config is True:
        from apcore.observability.tracing import StdoutExporter

        _tracing_exporter = StdoutExporter()
        return TracingMiddleware(exporter=_tracing_exporter)

    exporter_name = config.get("exporter", "stdout")
    exporter = _resolve_tracing_exporter(exporter_name, config)
    _tracing_exporter = exporter

    kwargs: dict[str, Any] = {"exporter": exporter}
    if "sampling_rate" in config:
        kwargs["sampling_rate"] = config["sampling_rate"]
    if "sampling_strategy" in config:
        kwargs["sampling_strategy"] = config["sampling_strategy"]

    return TracingMiddleware(**kwargs)


def _resolve_tracing_exporter(name: str, config: dict) -> Any:
    """Resolve a tracing exporter by name or dotted path.

    Args:
        name: "stdout", "in_memory", "otlp", or a dotted import path.
        config: The full tracing config dict for OTLP options.

    Returns:
        An exporter instance.
    """
    if name == "stdout":
        from apcore.observability.tracing import StdoutExporter

        return StdoutExporter()
    if name == "in_memory":
        from apcore.observability.tracing import InMemoryExporter

        return InMemoryExporter()
    if name == "otlp":
        from apcore.observability.tracing import OTLPExporter

        kwargs: dict[str, Any] = {}
        if "otlp_endpoint" in config:
            kwargs["endpoint"] = config["otlp_endpoint"]
        if "otlp_service_name" in config:
            kwargs["service_name"] = config["otlp_service_name"]
        return OTLPExporter(**kwargs)

    # Dotted path import
    module_path, class_name = name.rsplit(".", 1)
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls()


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


def _create_metrics_collector(config: bool | dict) -> Any:
    """Create a MetricsCollector from settings.

    Args:
        config: True for defaults, or a dict with buckets.

    Returns:
        A MetricsCollector instance.
    """
    from apcore.observability.metrics import MetricsCollector

    if config is True:
        return MetricsCollector()

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
    """Reset the singleton executor. For testing only.

    Also shuts down the tracing exporter if one was created (important
    for OTLPExporter which needs to flush pending spans).
    """
    global _executor, _tracing_exporter
    with _executor_lock:
        if _tracing_exporter is not None:
            if hasattr(_tracing_exporter, "shutdown"):
                with contextlib.suppress(Exception):
                    _tracing_exporter.shutdown()
            _tracing_exporter = None
        _executor = None


def _reset_registry() -> None:
    """Reset the singleton registry. For testing only.

    This causes the next call to get_registry() to create a fresh
    Registry instance. Also resets the executor and context factory
    since they depend on the registry.
    """
    global _registry
    with _lock:
        _registry = None
    _reset_executor()
    _reset_context_factory()
    _reset_metrics_collector()
    _reset_embedded_server()

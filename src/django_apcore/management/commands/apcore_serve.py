"""apcore_serve management command.

Loads the apcore registry and starts an MCP server via apcore-mcp-python.

Usage:
    manage.py apcore_serve
    manage.py apcore_serve --transport streamable-http --host 0.0.0.0 --port 9090
    manage.py apcore_serve --name my-server
    manage.py apcore_serve --version 1.2.3
    manage.py apcore_serve --output-formatter apcore_toolkit.to_markdown
"""

from __future__ import annotations

import re
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_apcore.registry import get_registry
from django_apcore.settings import get_apcore_settings


def _resolve_output_formatter(dotted_path: str | None) -> Any:
    """Resolve an output_formatter dotted path to a callable.

    Args:
        dotted_path: Dotted path like 'apcore_toolkit.to_markdown', or None.

    Returns:
        The resolved callable, or None.
    """
    if not dotted_path:
        return None
    import importlib

    module_path, sep, attr_name = dotted_path.rpartition(".")
    if not sep or not module_path:
        return None
    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, attr_name)
    except (ImportError, AttributeError):
        return None


def serve(
    registry_or_executor: Any,
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    name: str = "apcore-mcp",
    version: str | None = None,
    on_startup: Any = None,
    on_shutdown: Any = None,
    validate_inputs: bool = False,
    metrics_collector: Any = None,
    log_level: str | None = None,
    tags: list[str] | None = None,
    prefix: str | None = None,
    explorer: bool = False,
    explorer_prefix: str = "/explorer",
    allow_execute: bool = False,
    authenticator: Any = None,
    output_formatter: Any = None,
) -> None:
    """Delegate to apcore_mcp.serve().

    This wrapper handles the lazy import of apcore-mcp-python.
    """
    try:
        from apcore_mcp import serve as apcore_serve
    except ImportError:
        raise ImportError(
            "apcore-mcp is required for apcore_serve. "
            "Install with: pip install django-apcore[mcp]"
        ) from None

    kwargs: dict[str, Any] = {
        "transport": transport,
        "host": host,
        "port": port,
        "name": name,
    }
    if version is not None:
        kwargs["version"] = version
    if on_startup is not None:
        kwargs["on_startup"] = on_startup
    if on_shutdown is not None:
        kwargs["on_shutdown"] = on_shutdown
    if validate_inputs:
        kwargs["validate_inputs"] = validate_inputs
    if metrics_collector is not None:
        kwargs["metrics_collector"] = metrics_collector
    if log_level is not None:
        kwargs["log_level"] = log_level
    if tags is not None:
        kwargs["tags"] = tags
    if prefix is not None:
        kwargs["prefix"] = prefix
    if explorer:
        kwargs["explorer"] = True
        kwargs["explorer_prefix"] = explorer_prefix
        kwargs["allow_execute"] = allow_execute
    if authenticator is not None:
        kwargs["authenticator"] = authenticator
    if output_formatter is not None:
        kwargs["output_formatter"] = output_formatter

    apcore_serve(registry_or_executor, **kwargs)


class Command(BaseCommand):
    help = "Start an MCP server with registered apcore modules."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--transport",
            "-t",
            type=str,
            default=None,
            choices=["stdio", "streamable-http", "sse"],
            help=(
                "MCP transport: 'stdio', 'streamable-http', or 'sse'. "
                "Default: APCORE_SERVE_TRANSPORT setting."
            ),
        )
        parser.add_argument(
            "--host",
            type=str,
            default=None,
            help="Host for HTTP transports. Default: APCORE_SERVE_HOST setting.",
        )
        parser.add_argument(
            "--port",
            "-p",
            type=int,
            default=None,
            help="Port for HTTP transports. Default: APCORE_SERVE_PORT setting.",
        )
        parser.add_argument(
            "--name",
            type=str,
            default=None,
            help="MCP server name. Default: APCORE_SERVER_NAME setting.",
        )
        parser.add_argument(
            "--server-version",
            type=str,
            default=None,
            dest="server_version",
            help="Server version. Default: APCORE_SERVER_VERSION setting.",
        )
        parser.add_argument(
            "--validate-inputs",
            action="store_true",
            default=None,
            help="Enable input validation on the MCP server.",
        )
        parser.add_argument(
            "--metrics",
            action="store_true",
            default=None,
            help="Enable Prometheus /metrics endpoint.",
        )
        parser.add_argument(
            "--log-level",
            type=str,
            default=None,
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="Set MCP server log level.",
        )
        parser.add_argument(
            "--tags",
            type=str,
            default=None,
            help="Filter modules by tags (comma-separated).",
        )
        parser.add_argument(
            "--prefix",
            type=str,
            default=None,
            help="Filter modules by ID prefix.",
        )
        parser.add_argument(
            "--explorer",
            action="store_true",
            default=None,
            help="Enable the browser-based Tool Explorer UI (HTTP transports only).",
        )
        parser.add_argument(
            "--explorer-prefix",
            type=str,
            default=None,
            dest="explorer_prefix",
            help='URL prefix for the explorer UI (default: "/explorer").',
        )
        parser.add_argument(
            "--allow-execute",
            action="store_true",
            default=None,
            dest="allow_execute",
            help="Allow tool execution from the explorer UI.",
        )
        parser.add_argument(
            "--jwt-secret",
            type=str,
            default=None,
            dest="jwt_secret",
            help="JWT secret/key for authentication. "
            "Default: APCORE_JWT_SECRET setting.",
        )
        parser.add_argument(
            "--jwt-algorithm",
            type=str,
            default=None,
            dest="jwt_algorithm",
            help='JWT algorithm (default: "HS256"). '
            "Default: APCORE_JWT_ALGORITHM setting.",
        )
        parser.add_argument(
            "--jwt-audience",
            type=str,
            default=None,
            dest="jwt_audience",
            help="Expected JWT audience claim. Default: APCORE_JWT_AUDIENCE setting.",
        )
        parser.add_argument(
            "--jwt-issuer",
            type=str,
            default=None,
            dest="jwt_issuer",
            help="Expected JWT issuer claim. Default: APCORE_JWT_ISSUER setting.",
        )
        parser.add_argument(
            "--output-formatter",
            type=str,
            default=None,
            dest="output_formatter",
            help=(
                "Dotted path to output formatter callable "
                "(e.g., 'apcore_toolkit.to_markdown'). "
                "Default: APCORE_OUTPUT_FORMATTER setting."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        verbosity = options["verbosity"]

        # Load settings
        settings = get_apcore_settings()

        # Resolve arguments with settings fallbacks
        transport = options["transport"] or settings.serve_transport
        host = options["host"] or settings.serve_host
        port = options["port"] if options["port"] is not None else settings.serve_port
        name = options["name"] or settings.server_name
        version = options["server_version"] or settings.server_version

        # Resolve v0.1.0 arguments with settings fallbacks
        validate_inputs_flag = options.get("validate_inputs")
        validate_inputs = (
            validate_inputs_flag
            if validate_inputs_flag is not None
            else (settings.serve_validate_inputs or settings.validate_inputs)
        )

        metrics_flag = options.get("metrics")
        serve_metrics = (
            metrics_flag if metrics_flag is not None else settings.serve_metrics
        )

        log_level = options.get("log_level") or settings.serve_log_level

        tags_str = options.get("tags")
        tags: list[str] | None
        if tags_str:
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        else:
            tags = settings.serve_tags

        prefix = options.get("prefix") or settings.serve_prefix

        # Validate port range
        if not (1 <= port <= 65535):
            raise CommandError(f"--port must be between 1 and 65535. Got: {port}.")

        # Validate name: 1-100 chars, alphanumeric/hyphens/underscores
        if not name or len(name) > 100 or not re.match(r"^[a-zA-Z0-9_-]+$", name):
            raise CommandError(
                "--name must be 1-100 characters, "
                "alphanumeric, hyphens, and underscores only."
            )

        # Load registry or executor
        if verbosity >= 1:
            self.stdout.write("[django-apcore] Loading apcore registry...")

        # Use executor if any executor-related settings are configured
        use_executor = (
            settings.middlewares
            or settings.acl_path
            or settings.executor_config
            or settings.observability_logging
            or settings.tracing
            or settings.metrics
        )

        if use_executor:
            from django_apcore.registry import get_executor

            registry_or_executor = get_executor()
        else:
            registry_or_executor = get_registry()

        # Check for registered modules
        registry = get_registry()
        module_count = registry.count

        if module_count == 0:
            raise CommandError(
                "No apcore modules registered. "
                "Run 'manage.py apcore_scan' first or define modules "
                "with @module decorator."
            )

        if verbosity >= 1:
            self.stdout.write(f"[django-apcore] {module_count} modules registered.")
            self.stdout.write(
                f"[django-apcore] Starting MCP server '{name}' via {transport}..."
            )

        if transport in ("streamable-http", "sse") and host == "0.0.0.0":
            self.stderr.write(
                "[django-apcore] WARNING: Binding to 0.0.0.0 exposes the MCP "
                "server to all network interfaces. This is a security risk if "
                "the server is not behind a firewall."
            )

        stdout = self.stdout

        def on_startup() -> None:
            if verbosity >= 1:
                stdout.write("[django-apcore] Server ready.")

        def on_shutdown() -> None:
            if verbosity >= 1:
                stdout.write("[django-apcore] Server stopped.")

        # Resolve metrics_collector
        metrics_collector = None
        if serve_metrics:
            from django_apcore.registry import get_metrics_collector

            metrics_collector = get_metrics_collector()

        # Resolve explorer settings
        explorer_flag = options.get("explorer")
        explorer_enabled = (
            explorer_flag if explorer_flag is not None else settings.explorer_enabled
        )

        explorer_prefix_arg = options.get("explorer_prefix")
        explorer_prefix = (
            explorer_prefix_arg
            if explorer_prefix_arg is not None
            else settings.explorer_prefix
        )

        allow_execute_flag = options.get("allow_execute")
        allow_execute = (
            allow_execute_flag
            if allow_execute_flag is not None
            else settings.explorer_allow_execute
        )

        if (
            explorer_enabled
            and transport in ("streamable-http", "sse")
            and verbosity >= 1
        ):
            self.stdout.write(
                f"[django-apcore] Tool Explorer enabled at {explorer_prefix}"
            )

        # Resolve JWT authentication
        jwt_secret = (
            options.get("jwt_secret")
            if options.get("jwt_secret") is not None
            else settings.jwt_secret
        )
        authenticator = None
        if jwt_secret is not None:
            jwt_algorithm = (
                options.get("jwt_algorithm")
                if options.get("jwt_algorithm") is not None
                else settings.jwt_algorithm
            )
            jwt_audience = (
                options.get("jwt_audience")
                if options.get("jwt_audience") is not None
                else settings.jwt_audience
            )
            jwt_issuer = (
                options.get("jwt_issuer")
                if options.get("jwt_issuer") is not None
                else settings.jwt_issuer
            )

            try:
                from apcore_mcp.auth import JWTAuthenticator
            except ImportError:
                raise CommandError(
                    "apcore-mcp >= 0.7.0 is required for JWT authentication. "
                    "Install with: pip install 'apcore-mcp>=0.10.0'"
                ) from None

            authenticator = JWTAuthenticator(
                jwt_secret,
                algorithms=[jwt_algorithm],
                audience=jwt_audience,
                issuer=jwt_issuer,
            )

            if verbosity >= 1:
                self.stdout.write("[django-apcore] JWT authentication enabled.")

        # Resolve output formatter
        output_formatter_path = (
            options.get("output_formatter")
            if options.get("output_formatter") is not None
            else settings.output_formatter
        )
        output_formatter = _resolve_output_formatter(output_formatter_path)
        if output_formatter_path and output_formatter is None:
            self.stderr.write(
                f"[django-apcore] WARNING: Could not resolve output formatter "
                f"'{output_formatter_path}'. Results will be raw JSON."
            )
        elif output_formatter is not None and verbosity >= 1:
            self.stdout.write(
                f"[django-apcore] Output formatter: {output_formatter_path}"
            )

        # Delegate to apcore-mcp
        try:
            serve(
                registry_or_executor,
                transport=transport,
                host=host,
                port=port,
                name=name,
                version=version,
                on_startup=on_startup,
                on_shutdown=on_shutdown,
                validate_inputs=validate_inputs,
                metrics_collector=metrics_collector,
                log_level=log_level,
                tags=tags,
                prefix=prefix,
                explorer=explorer_enabled,
                explorer_prefix=explorer_prefix,
                allow_execute=allow_execute,
                authenticator=authenticator,
                output_formatter=output_formatter,
            )
        except ImportError as e:
            msg = (
                str(e)
                if str(e)
                else (
                    "apcore-mcp is required for apcore_serve. "
                    "Install with: pip install django-apcore[mcp]"
                )
            )
            raise CommandError(msg) from e

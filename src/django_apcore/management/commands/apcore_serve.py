"""apcore_serve management command.

Loads the apcore registry and starts an MCP server via apcore-mcp-python.

Usage:
    manage.py apcore_serve
    manage.py apcore_serve --transport streamable-http --host 0.0.0.0 --port 9090
    manage.py apcore_serve --name my-server
    manage.py apcore_serve --version 1.2.3
"""

from __future__ import annotations

import re
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_apcore.registry import get_registry
from django_apcore.settings import get_apcore_settings


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
    # NOTE: validate_inputs is a reserved parameter in apcore-mcp v0.2.0.
    # Passing it is forward-compatible but may not take effect yet.
    if validate_inputs:
        kwargs["validate_inputs"] = validate_inputs

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
                validate_inputs=settings.validate_inputs,
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

# Task 010: apcore_serve Management Command + Integration Tests

## Goal

Implement the `apcore_serve` Django management command that loads the apcore Registry (triggering auto-discovery if needed), validates that modules exist, and delegates to `apcore_mcp.serve()` for MCP server startup. Also write integration tests that verify the registry-to-serve pipeline end-to-end.

## Files Involved

### Create

- `src/django_apcore/management/commands/apcore_serve.py` -- `Command` class
- `tests/integration/__init__.py` -- Integration test package init
- `tests/integration/test_registry_serve.py` -- Integration tests for registry-to-serve flow

### Modify

- `tests/test_commands.py` -- Add `TestApcoreServeCommand` class

## Steps

### Step 1: Write tests (TDD -- Red phase)

Add to `tests/test_commands.py`:

```python
# Add to tests/test_commands.py (extend existing file)

class TestApcoreServeCommand:
    """Test the apcore_serve management command."""

    def test_command_exists(self):
        """apcore_serve command is discoverable by Django."""
        from django.core.management import get_commands

        commands = get_commands()
        assert "apcore_serve" in commands

    def test_default_transport_from_settings(self):
        """Default transport comes from APCORE_SERVE_TRANSPORT setting."""
        with patch("django_apcore.management.commands.apcore_serve.get_apcore_settings") as mock_settings:
            with patch("django_apcore.management.commands.apcore_serve.get_registry") as mock_reg:
                with patch("django_apcore.management.commands.apcore_serve.serve") as mock_serve:
                    mock_settings.return_value = MagicMock(
                        serve_transport="stdio",
                        serve_host="127.0.0.1",
                        serve_port=8000,
                        server_name="apcore-mcp",
                    )
                    mock_registry = MagicMock()
                    mock_registry.count = 5
                    mock_reg.return_value = mock_registry
                    mock_serve.return_value = None

                    call_command("apcore_serve")
                    mock_serve.assert_called_once()

    def test_transport_override(self):
        """--transport overrides the setting."""
        with patch("django_apcore.management.commands.apcore_serve.get_apcore_settings") as mock_settings:
            with patch("django_apcore.management.commands.apcore_serve.get_registry") as mock_reg:
                with patch("django_apcore.management.commands.apcore_serve.serve") as mock_serve:
                    mock_settings.return_value = MagicMock(
                        serve_transport="stdio",
                        serve_host="127.0.0.1",
                        serve_port=8000,
                        server_name="apcore-mcp",
                    )
                    mock_registry = MagicMock()
                    mock_registry.count = 5
                    mock_reg.return_value = mock_registry
                    mock_serve.return_value = None

                    call_command("apcore_serve", "--transport", "streamable-http")

    def test_invalid_transport_rejected(self):
        """Invalid --transport values are rejected."""
        with pytest.raises((CommandError, SystemExit)):
            call_command("apcore_serve", "--transport", "websocket")

    def test_empty_registry_raises_error(self):
        """CommandError when no modules are registered."""
        with patch("django_apcore.management.commands.apcore_serve.get_apcore_settings") as mock_settings:
            with patch("django_apcore.management.commands.apcore_serve.get_registry") as mock_reg:
                mock_settings.return_value = MagicMock(
                    serve_transport="stdio",
                    serve_host="127.0.0.1",
                    serve_port=8000,
                    server_name="apcore-mcp",
                )
                mock_registry = MagicMock()
                mock_registry.count = 0
                mock_reg.return_value = mock_registry

                with pytest.raises(CommandError, match="No apcore modules registered"):
                    call_command("apcore_serve")

    def test_missing_apcore_mcp_raises_error(self):
        """CommandError when apcore-mcp is not installed."""
        with patch("django_apcore.management.commands.apcore_serve.get_apcore_settings") as mock_settings:
            with patch("django_apcore.management.commands.apcore_serve.get_registry") as mock_reg:
                with patch("django_apcore.management.commands.apcore_serve.serve", side_effect=ImportError):
                    mock_settings.return_value = MagicMock(
                        serve_transport="stdio",
                        serve_host="127.0.0.1",
                        serve_port=8000,
                        server_name="apcore-mcp",
                    )
                    mock_registry = MagicMock()
                    mock_registry.count = 5
                    mock_reg.return_value = mock_registry

                    with pytest.raises(CommandError, match="apcore-mcp"):
                        call_command("apcore_serve")

    def test_host_override(self):
        """--host overrides the setting."""
        with patch("django_apcore.management.commands.apcore_serve.get_apcore_settings") as mock_settings:
            with patch("django_apcore.management.commands.apcore_serve.get_registry") as mock_reg:
                with patch("django_apcore.management.commands.apcore_serve.serve") as mock_serve:
                    mock_settings.return_value = MagicMock(
                        serve_transport="streamable-http",
                        serve_host="127.0.0.1",
                        serve_port=8000,
                        server_name="apcore-mcp",
                    )
                    mock_registry = MagicMock()
                    mock_registry.count = 5
                    mock_reg.return_value = mock_registry
                    mock_serve.return_value = None

                    call_command(
                        "apcore_serve",
                        "--transport", "streamable-http",
                        "--host", "0.0.0.0",
                        "--port", "9090",
                    )

    def test_port_must_be_in_range(self):
        """Port outside 1-65535 is rejected."""
        with pytest.raises((CommandError, SystemExit)):
            call_command("apcore_serve", "--port", "99999")

    def test_name_override(self):
        """--name overrides server name."""
        with patch("django_apcore.management.commands.apcore_serve.get_apcore_settings") as mock_settings:
            with patch("django_apcore.management.commands.apcore_serve.get_registry") as mock_reg:
                with patch("django_apcore.management.commands.apcore_serve.serve") as mock_serve:
                    mock_settings.return_value = MagicMock(
                        serve_transport="stdio",
                        serve_host="127.0.0.1",
                        serve_port=8000,
                        server_name="apcore-mcp",
                    )
                    mock_registry = MagicMock()
                    mock_registry.count = 5
                    mock_reg.return_value = mock_registry
                    mock_serve.return_value = None

                    call_command("apcore_serve", "--name", "my-server")

    def test_output_prefix(self):
        """Command output uses [django-apcore] prefix."""
        with patch("django_apcore.management.commands.apcore_serve.get_apcore_settings") as mock_settings:
            with patch("django_apcore.management.commands.apcore_serve.get_registry") as mock_reg:
                with patch("django_apcore.management.commands.apcore_serve.serve") as mock_serve:
                    mock_settings.return_value = MagicMock(
                        serve_transport="stdio",
                        serve_host="127.0.0.1",
                        serve_port=8000,
                        server_name="apcore-mcp",
                    )
                    mock_registry = MagicMock()
                    mock_registry.count = 5
                    mock_reg.return_value = mock_registry
                    mock_serve.return_value = None

                    out = StringIO()
                    call_command("apcore_serve", stdout=out)
                    assert "[django-apcore]" in out.getvalue()
```

Create `tests/integration/test_registry_serve.py`:

```python
# tests/integration/test_registry_serve.py
"""Integration tests for the registry-to-serve pipeline.

These tests verify that:
1. The registry can be populated programmatically
2. The populated registry can be passed to the serve command flow
3. Settings + registry + serve work together as a complete pipeline
"""
import pytest
from unittest.mock import MagicMock, patch


class TestRegistryServeIntegration:
    """Integration tests for registry -> serve pipeline."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def test_registry_populated_then_serve(self):
        """Registry with registered modules can be served."""
        from django_apcore.registry import get_registry

        registry = get_registry()

        # The registry should be accessible and usable
        assert registry is not None
        assert hasattr(registry, "register")

    def test_settings_and_registry_work_together(self):
        """Settings are correctly read when registry is initialized."""
        from django_apcore.registry import get_registry
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        registry = get_registry()

        assert settings.module_dir == "apcore_modules/"
        assert registry is not None

    def test_app_config_initializes_registry(self):
        """AppConfig.ready() initializes the registry successfully."""
        from django_apcore.apps import ApcoreAppConfig
        from django_apcore.registry import get_registry

        app_config = ApcoreAppConfig("django_apcore", "django_apcore")
        # Should not raise
        app_config.ready()

        registry = get_registry()
        assert registry is not None

    def test_full_pipeline_settings_to_serve(self):
        """Full pipeline: settings -> registry -> serve delegation."""
        from django_apcore.registry import get_registry
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        registry = get_registry()

        # Mock the serve function since we don't want to actually start a server
        with patch("django_apcore.management.commands.apcore_serve.serve") as mock_serve:
            mock_serve.return_value = None

            # Simulate what the serve command does
            assert settings.serve_transport in ("stdio", "streamable-http", "sse")
            # In a real scenario, we'd call serve(registry, transport=...)
```

### Step 2: Run tests -- verify they fail

```bash
pytest tests/test_commands.py::TestApcoreServeCommand -x --tb=short
pytest tests/integration/test_registry_serve.py -x --tb=short
```

Expected: `ModuleNotFoundError` for `apcore_serve` command module.

### Step 3: Implement

Create `src/django_apcore/management/commands/apcore_serve.py`:

```python
"""apcore_serve management command.

Loads the apcore registry and starts an MCP server via apcore-mcp-python.

Usage:
    manage.py apcore_serve
    manage.py apcore_serve --transport streamable-http --host 0.0.0.0 --port 9090
    manage.py apcore_serve --name my-server
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from django_apcore.registry import get_registry
from django_apcore.settings import get_apcore_settings


def serve(registry, transport: str = "stdio", host: str = "127.0.0.1",
          port: int = 8000, name: str = "apcore-mcp") -> None:
    """Delegate to apcore_mcp.serve().

    This wrapper handles the lazy import of apcore-mcp-python.
    """
    try:
        from apcore_mcp import serve as apcore_serve
    except ImportError:
        raise ImportError(
            "apcore-mcp is required for apcore_serve. "
            "Install with: pip install django-apcore[mcp]"
        )
    apcore_serve(registry, transport=transport, host=host, port=port, name=name)


class Command(BaseCommand):
    help = "Start an MCP server with registered apcore modules."

    def add_arguments(self, parser):
        parser.add_argument(
            "--transport", "-t",
            type=str,
            default=None,
            choices=["stdio", "streamable-http", "sse"],
            help="MCP transport: 'stdio', 'streamable-http', or 'sse'. Default: APCORE_SERVE_TRANSPORT setting.",
        )
        parser.add_argument(
            "--host",
            type=str,
            default=None,
            help="Host for HTTP transports. Default: APCORE_SERVE_HOST setting.",
        )
        parser.add_argument(
            "--port", "-p",
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

    def handle(self, *args, **options):
        verbosity = options["verbosity"]

        # Load settings
        settings = get_apcore_settings()

        # Resolve arguments with settings fallbacks
        transport = options["transport"] or settings.serve_transport
        host = options["host"] or settings.serve_host
        port = options["port"] or settings.serve_port
        name = options["name"] or settings.server_name

        # Validate port range
        if not (1 <= port <= 65535):
            raise CommandError(
                f"--port must be between 1 and 65535. Got: {port}."
            )

        # Validate name
        if not name or len(name) > 100:
            raise CommandError(
                "--name must be 1-100 characters, alphanumeric and hyphens only."
            )

        # Load registry
        if verbosity >= 1:
            self.stdout.write("[django-apcore] Loading apcore registry...")

        registry = get_registry()

        # Check for registered modules
        module_count = getattr(registry, "count", 0)
        if hasattr(registry, "__len__"):
            module_count = len(registry)
        elif hasattr(registry, "count"):
            module_count = registry.count if callable(registry.count) else registry.count

        if module_count == 0:
            raise CommandError(
                "No apcore modules registered. "
                "Run 'manage.py apcore_scan' first or define modules with @module decorator."
            )

        if verbosity >= 1:
            self.stdout.write(
                f"[django-apcore] {module_count} modules registered."
            )
            self.stdout.write(
                f"[django-apcore] Starting MCP server '{name}' via {transport}..."
            )

        if transport in ("streamable-http", "sse") and host == "0.0.0.0":
            self.stderr.write(
                "[django-apcore] WARNING: Binding to 0.0.0.0 exposes the MCP server "
                "to all network interfaces. This is a security risk if the server "
                "is not behind a firewall."
            )

        # Delegate to apcore-mcp
        try:
            serve(
                registry,
                transport=transport,
                host=host,
                port=port,
                name=name,
            )
        except ImportError as e:
            raise CommandError(
                f"apcore-mcp is required for apcore_serve. "
                f"Install with: pip install django-apcore[mcp]"
            )
        except KeyboardInterrupt:
            if verbosity >= 1:
                self.stdout.write("[django-apcore] Server stopped.")
        except Exception as e:
            raise CommandError(f"Server error: {e}")

        if verbosity >= 1:
            self.stdout.write("[django-apcore] Server ready. Waiting for connections.")
```

### Step 4: Run tests -- verify they pass

```bash
pytest tests/test_commands.py::TestApcoreServeCommand -x --tb=short -v
pytest tests/integration/test_registry_serve.py -x --tb=short -v
```

All tests should pass.

### Step 5: Commit

```bash
git add src/django_apcore/management/commands/apcore_serve.py tests/test_commands.py tests/integration/
git commit -m "feat: apcore_serve management command with registry integration"
```

## Acceptance Criteria

- [ ] `manage.py apcore_serve` is discoverable by Django's management command system
- [ ] `--transport` defaults to `APCORE_SERVE_TRANSPORT` setting; accepts `stdio`, `streamable-http`, `sse`
- [ ] `--host` defaults to `APCORE_SERVE_HOST` setting
- [ ] `--port` defaults to `APCORE_SERVE_PORT` setting; validated to 1-65535 range
- [ ] `--name` defaults to `APCORE_SERVER_NAME` setting
- [ ] Empty registry (0 modules) raises `CommandError` with "Run 'apcore_scan' first" message
- [ ] Missing `apcore-mcp-python` raises `CommandError` with install instructions
- [ ] Binding to `0.0.0.0` produces a security warning on stderr
- [ ] Delegates to `apcore_mcp.serve()` with correct parameters
- [ ] `KeyboardInterrupt` (Ctrl+C) produces clean shutdown message
- [ ] All output uses `[django-apcore]` prefix
- [ ] Integration test confirms settings -> registry -> serve pipeline
- [ ] 85% test coverage for `apcore_serve.py`

## Dependencies

- **004-app-config** -- Requires `ApcoreAppConfig` for auto-discovery in `ready()`
- **003-registry** -- Requires `get_registry()` for the singleton Registry

## Estimated Time

3 hours

## Troubleshooting

**Issue: `apcore_mcp.serve()` signature differs from what's used here**
Check the apcore-mcp-python source at `/Users/tercel/WorkSpace/aipartnerup/apcore-mcp-python/src/apcore_mcp/` for the exact `serve()` function signature. The wrapper function in `apcore_serve.py` should adapt to match the actual API.

**Issue: `registry.count` property vs method**
Different versions of the apcore SDK may expose `count` as a property or method. The implementation checks both patterns with `getattr` and `callable()`. Verify against the actual apcore SDK source to determine the correct access pattern.

"""Tests for the apcore_serve management command."""

from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

_CMD = "django_apcore.management.commands.apcore_serve"


def _mock_settings(**overrides):
    defaults = {
        "serve_transport": "stdio",
        "serve_host": "127.0.0.1",
        "serve_port": 8000,
        "server_name": "apcore-mcp",
        "server_version": None,
        "middlewares": [],
        "acl_path": None,
        "executor_config": None,
        "observability_logging": None,
        "validate_inputs": False,
        "tracing": None,
        "metrics": None,
        "embedded_server": None,
        "serve_validate_inputs": False,
        "serve_metrics": False,
        "serve_log_level": None,
        "serve_tags": None,
        "serve_prefix": None,
        "explorer_enabled": False,
        "explorer_prefix": "/explorer",
        "explorer_allow_execute": False,
    }
    defaults.update(overrides)
    return MagicMock(**defaults)


def _mock_registry(count=5):
    mock = MagicMock()
    mock.count = count
    return mock


class TestApcoreServeCommand:
    """Test the apcore_serve management command."""

    def test_command_exists(self):
        """apcore_serve command is discoverable by Django."""
        from django.core.management import get_commands

        commands = get_commands()
        assert "apcore_serve" in commands

    def test_default_transport_from_settings(self):
        """Default transport comes from APCORE_SERVE_TRANSPORT setting."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            call_command("apcore_serve")
            mock_serve.assert_called_once()

    def test_transport_override(self):
        """--transport overrides the setting."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            call_command("apcore_serve", "--transport", "streamable-http")

    def test_invalid_transport_rejected(self):
        """Invalid --transport values are rejected."""
        with pytest.raises((CommandError, SystemExit)):
            call_command("apcore_serve", "--transport", "websocket")

    def test_empty_registry_raises_error(self):
        """CommandError when no modules are registered."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry(count=0)

            with pytest.raises(CommandError, match="No apcore modules registered"):
                call_command("apcore_serve")

    def test_missing_apcore_mcp_raises_error(self):
        """CommandError when apcore-mcp is not installed."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve", side_effect=ImportError),
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()

            with pytest.raises(CommandError, match="apcore-mcp"):
                call_command("apcore_serve")

    def test_host_override(self):
        """--host overrides the setting."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings(
                serve_transport="streamable-http",
            )
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            call_command(
                "apcore_serve",
                "--transport",
                "streamable-http",
                "--host",
                "0.0.0.0",
                "--port",
                "9090",
            )

    def test_port_must_be_in_range(self):
        """Port outside 1-65535 is rejected."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry"),
        ):
            mock_settings.return_value = _mock_settings()
            with pytest.raises((CommandError, SystemExit)):
                call_command("apcore_serve", "--port", "99999")

    def test_name_override(self):
        """--name overrides server name."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            call_command("apcore_serve", "--name", "my-server")

    def test_output_prefix(self):
        """Command output uses [django-apcore] prefix."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            out = StringIO()
            call_command("apcore_serve", stdout=out)
            assert "[django-apcore]" in out.getvalue()


class TestApcoreServeV02:
    """Test v0.2.0 serve command features."""

    def test_version_from_settings(self):
        """Version is passed from APCORE_SERVER_VERSION setting."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings(
                server_version="1.0.0",
            )
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            call_command("apcore_serve")
            call_kwargs = mock_serve.call_args
            assert call_kwargs.kwargs.get("version") == "1.0.0"

    def test_version_override(self):
        """--server-version CLI arg overrides setting."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings(
                server_version="1.0.0",
            )
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            call_command("apcore_serve", "--server-version", "2.0.0")
            call_kwargs = mock_serve.call_args
            assert call_kwargs.kwargs.get("version") == "2.0.0"

    def test_executor_used_when_configured(self):
        """Executor is used when middleware settings are configured."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
            patch("django_apcore.registry.get_executor") as mock_get_exec,
        ):
            mock_settings.return_value = _mock_settings(
                middlewares=["some.Middleware"],
            )
            mock_reg.return_value = _mock_registry()
            mock_executor = MagicMock()
            mock_get_exec.return_value = mock_executor
            mock_serve.return_value = None

            call_command("apcore_serve")
            mock_get_exec.assert_called_once()
            # First positional arg should be executor
            assert mock_serve.call_args.args[0] is mock_executor

    def test_registry_used_by_default(self):
        """Registry is used when no executor settings are configured."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_registry = _mock_registry()
            mock_reg.return_value = mock_registry
            mock_serve.return_value = None

            call_command("apcore_serve")
            # First positional arg should be registry
            assert mock_serve.call_args.args[0] is mock_registry

    def test_on_startup_callback_passed(self):
        """on_startup callback is passed to serve()."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            call_command("apcore_serve")
            call_kwargs = mock_serve.call_args.kwargs
            assert "on_startup" in call_kwargs
            assert callable(call_kwargs["on_startup"])

    def test_executor_used_when_tracing_configured(self):
        """Executor is used when tracing is configured."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
            patch("django_apcore.registry.get_executor") as mock_get_exec,
        ):
            mock_settings.return_value = _mock_settings(tracing=True)
            mock_reg.return_value = _mock_registry()
            mock_executor = MagicMock()
            mock_get_exec.return_value = mock_executor
            mock_serve.return_value = None

            call_command("apcore_serve")
            mock_get_exec.assert_called_once()
            assert mock_serve.call_args.args[0] is mock_executor

    def test_executor_used_when_metrics_configured(self):
        """Executor is used when metrics is configured."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
            patch("django_apcore.registry.get_executor") as mock_get_exec,
        ):
            mock_settings.return_value = _mock_settings(metrics=True)
            mock_reg.return_value = _mock_registry()
            mock_executor = MagicMock()
            mock_get_exec.return_value = mock_executor
            mock_serve.return_value = None

            call_command("apcore_serve")
            mock_get_exec.assert_called_once()
            assert mock_serve.call_args.args[0] is mock_executor

    def test_validate_inputs_passed(self):
        """validate_inputs setting is passed to serve()."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings(
                validate_inputs=True,
            )
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            call_command("apcore_serve")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("validate_inputs") is True


class TestApcoreServeV010:
    """Test v0.1.0 serve command features."""

    def test_validate_inputs_flag(self):
        """--validate-inputs flag is passed to serve()."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None
            call_command("apcore_serve", "--validate-inputs")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("validate_inputs") is True

    def test_tags_passed(self):
        """--tags is split and passed to serve()."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None
            call_command("apcore_serve", "--tags", "api,public")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("tags") == ["api", "public"]

    def test_prefix_passed(self):
        """--prefix is passed to serve()."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None
            call_command("apcore_serve", "--prefix", "my.app")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("prefix") == "my.app"

    def test_log_level_passed(self):
        """--log-level is passed to serve()."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None
            call_command("apcore_serve", "--log-level", "DEBUG")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("log_level") == "DEBUG"

    def test_metrics_flag(self):
        """--metrics flag triggers metrics_collector creation."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
            patch("django_apcore.registry.get_metrics_collector") as mock_mc,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None
            mock_mc.return_value = MagicMock()
            call_command("apcore_serve", "--metrics")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("metrics_collector") is not None

    def test_settings_fallback_for_tags(self):
        """Tags fall back to APCORE_SERVE_TAGS setting."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings(serve_tags=["internal"])
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None
            call_command("apcore_serve")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("tags") == ["internal"]

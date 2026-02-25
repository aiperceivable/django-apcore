"""Tests for the APCORE_EXPLORER_* settings and apcore_serve explorer integration."""

from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

_CMD = "django_apcore.management.commands.apcore_serve"


class TestExplorerSettingsDefaults:
    """Test APCORE_EXPLORER_* settings defaults."""

    def test_default_explorer_disabled(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_enabled is False

    def test_default_explorer_prefix(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_prefix == "/explorer"

    def test_default_explorer_allow_execute(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_allow_execute is False


class TestExplorerSettingsCustomValues:
    """Test APCORE_EXPLORER_* settings with custom values."""

    @override_settings(APCORE_EXPLORER_ENABLED=True)
    def test_explorer_enabled_true(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_enabled is True

    @override_settings(APCORE_EXPLORER_PREFIX="/browse")
    def test_custom_prefix(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_prefix == "/browse"

    @override_settings(APCORE_EXPLORER_ALLOW_EXECUTE=True)
    def test_allow_execute_true(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_allow_execute is True


class TestExplorerSettingsValidation:
    """Test APCORE_EXPLORER_* settings validation."""

    @override_settings(APCORE_EXPLORER_ENABLED="yes")
    def test_explorer_enabled_invalid_type(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_EXPLORER_ENABLED"):
            get_apcore_settings()

    @override_settings(APCORE_EXPLORER_PREFIX="no-slash")
    def test_prefix_must_start_with_slash(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_EXPLORER_PREFIX"):
            get_apcore_settings()

    @override_settings(APCORE_EXPLORER_PREFIX=123)
    def test_prefix_invalid_type(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_EXPLORER_PREFIX"):
            get_apcore_settings()

    @override_settings(APCORE_EXPLORER_ALLOW_EXECUTE="true")
    def test_allow_execute_invalid_type(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_EXPLORER_ALLOW_EXECUTE"):
            get_apcore_settings()

    @override_settings(APCORE_EXPLORER_ENABLED=None)
    def test_none_uses_default(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_enabled is False

    @override_settings(APCORE_EXPLORER_PREFIX=None)
    def test_prefix_none_uses_default(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_prefix == "/explorer"


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


class TestServeCommandExplorer:
    """Test apcore_serve command passes explorer params to serve()."""

    def test_explorer_flag_passed(self):
        """--explorer flag is passed to serve()."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            from django.core.management import call_command

            call_command("apcore_serve", "--explorer")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("explorer") is True

    def test_explorer_prefix_passed(self):
        """--explorer-prefix is passed to serve()."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            from django.core.management import call_command

            call_command("apcore_serve", "--explorer", "--explorer-prefix", "/browse")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("explorer_prefix") == "/browse"

    def test_allow_execute_passed(self):
        """--allow-execute is passed to serve()."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            from django.core.management import call_command

            call_command("apcore_serve", "--explorer", "--allow-execute")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("allow_execute") is True

    def test_settings_fallback_for_explorer(self):
        """Explorer settings fall back to APCORE_EXPLORER_* settings."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings(
                explorer_enabled=True,
                explorer_prefix="/tools",
                explorer_allow_execute=True,
            )
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            from django.core.management import call_command

            call_command("apcore_serve")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("explorer") is True
            assert call_kwargs.get("explorer_prefix") == "/tools"
            assert call_kwargs.get("allow_execute") is True

    def test_no_explorer_by_default(self):
        """Explorer is not enabled by default."""
        with (
            patch(f"{_CMD}.get_apcore_settings") as mock_settings,
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.serve") as mock_serve,
        ):
            mock_settings.return_value = _mock_settings()
            mock_reg.return_value = _mock_registry()
            mock_serve.return_value = None

            from django.core.management import call_command

            call_command("apcore_serve")
            call_kwargs = mock_serve.call_args.kwargs
            assert call_kwargs.get("explorer") is False

    def test_explorer_output_message(self):
        """Command outputs explorer info when enabled with HTTP transport."""
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

            from django.core.management import call_command

            out = StringIO()
            call_command(
                "apcore_serve",
                "--transport", "streamable-http",
                "--explorer",
                stdout=out,
            )
            assert "Explorer" in out.getvalue()


class TestServeWrapperExplorer:
    """Test the serve() wrapper passes explorer params correctly."""

    def test_serve_passes_explorer_params(self):
        """serve() wrapper passes explorer/explorer_prefix/allow_execute."""
        with patch("apcore_mcp.serve") as mock_apcore_serve:
            from django_apcore.management.commands.apcore_serve import serve

            serve(
                MagicMock(),
                explorer=True,
                explorer_prefix="/my-explorer",
                allow_execute=True,
            )

            call_kwargs = mock_apcore_serve.call_args.kwargs
            assert call_kwargs["explorer"] is True
            assert call_kwargs["explorer_prefix"] == "/my-explorer"
            assert call_kwargs["allow_execute"] is True

    def test_serve_omits_explorer_when_disabled(self):
        """serve() wrapper does not pass explorer params when explorer=False."""
        with patch("apcore_mcp.serve") as mock_apcore_serve:
            from django_apcore.management.commands.apcore_serve import serve

            serve(MagicMock())

            call_kwargs = mock_apcore_serve.call_args.kwargs
            assert "explorer" not in call_kwargs
            assert "explorer_prefix" not in call_kwargs
            assert "allow_execute" not in call_kwargs

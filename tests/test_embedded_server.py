"""Tests for embedded MCP server lifecycle."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import override_settings


class TestEmbeddedServer:
    """Test start_embedded_server() / stop_embedded_server()."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def test_returns_none_when_not_configured(self):
        """Returns None when APCORE_EMBEDDED_SERVER is not set."""
        from django_apcore.registry import start_embedded_server

        result = start_embedded_server()
        assert result is None

    @override_settings(APCORE_EMBEDDED_SERVER=True)
    @patch("apcore_mcp.MCPServer")
    def test_true_creates_server_with_defaults(self, mock_server_cls):
        """True creates MCPServer with serve_* defaults and calls .start()."""
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server

        from django_apcore.registry import start_embedded_server

        result = start_embedded_server()
        assert result is mock_server
        mock_server_cls.assert_called_once()
        mock_server.start.assert_called_once()

        # Check defaults were used
        call_kwargs = mock_server_cls.call_args.kwargs
        assert call_kwargs["transport"] == "stdio"
        assert call_kwargs["host"] == "127.0.0.1"
        assert call_kwargs["port"] == 9090
        assert call_kwargs["name"] == "apcore-mcp"

    @override_settings(
        APCORE_EMBEDDED_SERVER={
            "transport": "streamable-http",
            "host": "0.0.0.0",
            "port": 9000,
        }
    )
    @patch("apcore_mcp.MCPServer")
    def test_dict_config_overrides(self, mock_server_cls):
        """Dict config overrides transport/host/port."""
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server

        from django_apcore.registry import start_embedded_server

        start_embedded_server()
        call_kwargs = mock_server_cls.call_args.kwargs
        assert call_kwargs["transport"] == "streamable-http"
        assert call_kwargs["host"] == "0.0.0.0"
        assert call_kwargs["port"] == 9000

    @override_settings(APCORE_EMBEDDED_SERVER=True)
    def test_missing_apcore_mcp_logs_warning(self, caplog):
        """Missing apcore-mcp logs warning and returns None."""
        import logging
        import sys

        from django_apcore.registry import start_embedded_server

        # Temporarily hide apcore_mcp from sys.modules
        saved = sys.modules.get("apcore_mcp")
        sys.modules["apcore_mcp"] = None  # type: ignore[assignment]
        try:
            with caplog.at_level(logging.WARNING, logger="django_apcore"):
                result = start_embedded_server()
            assert result is None
        finally:
            if saved is not None:
                sys.modules["apcore_mcp"] = saved
            else:
                sys.modules.pop("apcore_mcp", None)

    @override_settings(APCORE_EMBEDDED_SERVER=True)
    @patch("apcore_mcp.MCPServer")
    def test_singleton_behavior(self, mock_server_cls):
        """Called twice returns the same MCPServer."""
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server

        from django_apcore.registry import start_embedded_server

        s1 = start_embedded_server()
        s2 = start_embedded_server()
        assert s1 is s2
        mock_server_cls.assert_called_once()

    @override_settings(APCORE_EMBEDDED_SERVER=True)
    @patch("apcore_mcp.MCPServer")
    def test_stop_calls_stop(self, mock_server_cls):
        """stop_embedded_server() calls .stop() on the server."""
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server

        from django_apcore.registry import (
            start_embedded_server,
            stop_embedded_server,
        )

        start_embedded_server()
        stop_embedded_server()
        mock_server.stop.assert_called_once()

    @override_settings(APCORE_EMBEDDED_SERVER=True)
    @patch("apcore_mcp.MCPServer")
    def test_reset_clears_singleton(self, mock_server_cls):
        """_reset_embedded_server() clears the singleton."""
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server

        from django_apcore.registry import (
            _reset_embedded_server,
            start_embedded_server,
        )

        start_embedded_server()
        _reset_embedded_server()

        import django_apcore.registry as reg

        assert reg._embedded_server is None

    def test_reset_registry_clears_embedded_server(self):
        """_reset_registry() also resets embedded server."""
        import django_apcore.registry as reg
        from django_apcore.registry import _reset_registry

        reg._embedded_server = MagicMock()
        _reset_registry()
        assert reg._embedded_server is None

    @override_settings(APCORE_EMBEDDED_SERVER=True, APCORE_JWT_SECRET="test-secret")
    @patch("apcore_mcp.auth.JWTAuthenticator")
    @patch("apcore_mcp.MCPServer")
    def test_jwt_settings_create_authenticator(self, mock_server_cls, mock_jwt_cls):
        """JWT settings create authenticator kwarg for MCPServer."""
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server
        mock_jwt = MagicMock()
        mock_jwt_cls.return_value = mock_jwt

        from django_apcore.registry import start_embedded_server

        start_embedded_server()
        mock_jwt_cls.assert_called_once_with(
            "test-secret",
            algorithms=["HS256"],
            audience=None,
            issuer=None,
        )
        call_kwargs = mock_server_cls.call_args.kwargs
        assert call_kwargs["authenticator"] is mock_jwt

    @override_settings(APCORE_EMBEDDED_SERVER=True)
    @patch("apcore_mcp.MCPServer")
    def test_no_authenticator_when_no_jwt_secret(self, mock_server_cls):
        """No authenticator when jwt_secret is None."""
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server

        from django_apcore.registry import start_embedded_server

        start_embedded_server()
        call_kwargs = mock_server_cls.call_args.kwargs
        assert "authenticator" not in call_kwargs
        # MCPServer defaults require_auth=True (apcore-mcp 0.14.0+); the
        # embedded server must opt out when there's no authenticator,
        # otherwise it would reject every request.
        assert call_kwargs["require_auth"] is False

    @override_settings(APCORE_EMBEDDED_SERVER=True, APCORE_JWT_SECRET="test-secret")
    @patch("apcore_mcp.auth.JWTAuthenticator")
    @patch("apcore_mcp.MCPServer")
    def test_require_auth_true_with_jwt(self, mock_server_cls, mock_jwt_cls):
        """require_auth is True when a JWT authenticator is configured."""
        mock_server_cls.return_value = MagicMock()
        mock_jwt_cls.return_value = MagicMock()

        from django_apcore.registry import start_embedded_server

        start_embedded_server()
        assert mock_server_cls.call_args.kwargs["require_auth"] is True

    @override_settings(
        APCORE_EMBEDDED_SERVER=True,
        APCORE_OUTPUT_FORMATTER="apcore_toolkit.to_markdown",
    )
    @patch("apcore_mcp.MCPServer")
    def test_output_formatter_resolved_and_passed(self, mock_server_cls):
        """apcore-mcp 0.17.0+ MCPServer accepts output_formatter; wire it through."""
        import apcore_toolkit

        mock_server_cls.return_value = MagicMock()

        from django_apcore.registry import start_embedded_server

        start_embedded_server()
        call_kwargs = mock_server_cls.call_args.kwargs
        assert call_kwargs["output_formatter"] is apcore_toolkit.to_markdown

    @override_settings(
        APCORE_EMBEDDED_SERVER=True,
        APCORE_OUTPUT_FORMATTER="apcore_toolkit.does_not_exist",
    )
    @patch("apcore_mcp.MCPServer")
    def test_unresolvable_output_formatter_warns(self, mock_server_cls, caplog):
        """An unresolvable formatter path is skipped with a warning, not a crash."""
        import logging

        mock_server_cls.return_value = MagicMock()

        from django_apcore.registry import start_embedded_server

        with caplog.at_level(logging.WARNING, logger="django_apcore"):
            start_embedded_server()
        call_kwargs = mock_server_cls.call_args.kwargs
        assert "output_formatter" not in call_kwargs
        assert any(
            "Could not resolve APCORE_OUTPUT_FORMATTER" in r.message
            for r in caplog.records
        )

    @override_settings(
        APCORE_EMBEDDED_SERVER=True,
        APCORE_SERVE_OUTPUT_FORMAT="csv",
        APCORE_SERVE_STRATEGY="performance",
        APCORE_SERVE_OBSERVABILITY=True,
        APCORE_SERVE_REDACT_OUTPUT=False,
        APCORE_SERVE_TRACE=True,
    )
    @patch("apcore_mcp.MCPServer")
    def test_pipeline_features_wired(self, mock_server_cls):
        """Pipeline/output settings reach MCPServer (apcore-mcp 0.17.0 parity)."""
        mock_server_cls.return_value = MagicMock()

        from django_apcore.registry import start_embedded_server

        start_embedded_server()
        call_kwargs = mock_server_cls.call_args.kwargs
        assert call_kwargs["output_format"] == "csv"
        assert call_kwargs["strategy"] == "performance"
        assert call_kwargs["observability"] is True
        assert call_kwargs["redact_output"] is False
        assert call_kwargs["trace"] is True

    @override_settings(
        APCORE_EMBEDDED_SERVER=True,
        APCORE_EXPLORER_ENABLED=True,
        APCORE_EXPLORER_PREFIX="/ui",
        APCORE_EXPLORER_ALLOW_EXECUTE=True,
        APCORE_EXPLORER_TITLE="My Explorer",
        APCORE_EXPLORER_PROJECT_NAME="demo",
        APCORE_EXPLORER_PROJECT_URL="https://example.com",
    )
    @patch("apcore_mcp.MCPServer")
    def test_explorer_features_wired(self, mock_server_cls):
        """Explorer settings reach MCPServer (apcore-mcp 0.17.0 parity)."""
        mock_server_cls.return_value = MagicMock()

        from django_apcore.registry import start_embedded_server

        start_embedded_server()
        call_kwargs = mock_server_cls.call_args.kwargs
        assert call_kwargs["explorer"] is True
        assert call_kwargs["explorer_prefix"] == "/ui"
        assert call_kwargs["allow_execute"] is True
        assert call_kwargs["explorer_title"] == "My Explorer"
        assert call_kwargs["explorer_project_name"] == "demo"
        assert call_kwargs["explorer_project_url"] == "https://example.com"

    @override_settings(
        APCORE_EMBEDDED_SERVER=True,
        APCORE_SERVE_REDACT_OUTPUT=True,
    )
    @patch("apcore_mcp.MCPServer")
    def test_redact_output_default_not_overridden(self, mock_server_cls):
        """redact_output defaults True in MCPServer; don't pass it when enabled."""
        mock_server_cls.return_value = MagicMock()

        from django_apcore.registry import start_embedded_server

        start_embedded_server()
        call_kwargs = mock_server_cls.call_args.kwargs
        assert "redact_output" not in call_kwargs

    @override_settings(
        APCORE_EMBEDDED_SERVER=True,
        APCORE_TASK_MAX_CONCURRENT=4,
        APCORE_TASK_MAX_TASKS=42,
    )
    @patch("apcore_mcp.MCPServer")
    def test_async_task_params_from_settings(self, mock_server_cls):
        """Async task bridge is sized from APCORE_TASK_* settings."""
        mock_server_cls.return_value = MagicMock()

        from django_apcore.registry import start_embedded_server

        start_embedded_server()
        call_kwargs = mock_server_cls.call_args.kwargs
        assert call_kwargs["async_max_concurrent"] == 4
        assert call_kwargs["async_max_tasks"] == 42

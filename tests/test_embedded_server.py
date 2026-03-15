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

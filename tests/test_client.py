# tests/test_client.py
"""Tests for the DjangoApcore unified entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestDjangoApcoreImport:
    """Test that DjangoApcore is importable from the top-level package."""

    def test_import_from_package(self):
        from django_apcore import DjangoApcore

        assert DjangoApcore is not None

    def test_import_from_client(self):
        from django_apcore.client import DjangoApcore

        assert DjangoApcore is not None

    def test_instantiation(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        assert app is not None


class TestDjangoApcoreProperties:
    """Test lazy property access to singletons."""

    def test_registry_property(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        with patch("django_apcore.registry.get_registry") as mock_get:
            mock_reg = MagicMock()
            mock_get.return_value = mock_reg
            assert app.registry is mock_reg

    def test_executor_property(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        with patch("django_apcore.registry.get_executor") as mock_get:
            mock_exec = MagicMock()
            mock_get.return_value = mock_exec
            assert app.executor is mock_exec

    def test_context_factory_property(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        with patch("django_apcore.registry.get_context_factory") as mock_get:
            mock_cf = MagicMock()
            mock_get.return_value = mock_cf
            assert app.context_factory is mock_cf

    def test_settings_property(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        s = app.settings
        assert s.module_dir == "apcore_modules/"


class TestDjangoApcoreCall:
    """Test module execution methods."""

    def test_call_with_request(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        mock_request = MagicMock()
        mock_context = MagicMock()
        mock_result = {"status": "ok"}

        with (
            patch("django_apcore.registry.get_executor") as mock_exec_get,
            patch("django_apcore.registry.get_context_factory") as mock_cf_get,
        ):
            mock_executor = MagicMock()
            mock_executor.call.return_value = mock_result
            mock_exec_get.return_value = mock_executor

            mock_cf = MagicMock()
            mock_cf.create_context.return_value = mock_context
            mock_cf_get.return_value = mock_cf

            result = app.call("test.module", {"key": "val"}, request=mock_request)

            assert result == mock_result
            mock_cf.create_context.assert_called_once_with(mock_request)
            mock_executor.call.assert_called_once_with(
                "test.module", {"key": "val"}, context=mock_context
            )

    def test_call_with_explicit_context(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        mock_context = MagicMock()

        with patch("django_apcore.registry.get_executor") as mock_exec_get:
            mock_executor = MagicMock()
            mock_executor.call.return_value = {"ok": True}
            mock_exec_get.return_value = mock_executor

            result = app.call("test.module", context=mock_context)

            mock_executor.call.assert_called_once_with(
                "test.module", {}, context=mock_context
            )
            assert result == {"ok": True}

    def test_call_without_context_or_request(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()

        with patch("django_apcore.registry.get_executor") as mock_exec_get:
            mock_executor = MagicMock()
            mock_executor.call.return_value = {}
            mock_exec_get.return_value = mock_executor

            app.call("test.module")

            mock_executor.call.assert_called_once_with("test.module", {}, context=None)


class TestDjangoApcoreListModules:
    """Test module listing and description."""

    def test_list_modules(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        with patch("django_apcore.registry.get_registry") as mock_get:
            mock_reg = MagicMock()
            mock_reg.list.return_value = ["a.b", "c.d"]
            mock_get.return_value = mock_reg

            result = app.list_modules(tags=["api"])
            assert result == ["a.b", "c.d"]
            mock_reg.list.assert_called_once_with(tags=["api"], prefix=None)

    def test_describe(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        with patch("django_apcore.registry.get_registry") as mock_get:
            mock_reg = MagicMock()
            mock_reg.describe.return_value = "List users"
            mock_get.return_value = mock_reg

            result = app.describe("users.list")
            assert result == "List users"


class TestDjangoApcoreScan:
    """Test scanning methods."""

    def test_scan_ninja(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        with patch("django_apcore.scanners.get_scanner") as mock_get:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = [MagicMock(module_id="api.users")]
            mock_get.return_value = mock_scanner

            result = app.scan(source="ninja", include="users")
            assert len(result) == 1
            mock_get.assert_called_once_with("ninja")
            mock_scanner.scan.assert_called_once_with(include="users", exclude=None)


class TestDjangoApcoreSingleton:
    """Test singleton pattern."""

    def test_get_instance_returns_same_object(self):
        from django_apcore.client import DjangoApcore

        DjangoApcore._reset_instance()
        try:
            a = DjangoApcore.get_instance()
            b = DjangoApcore.get_instance()
            assert a is b
        finally:
            DjangoApcore._reset_instance()

    def test_reset_instance(self):
        from django_apcore.client import DjangoApcore

        DjangoApcore._reset_instance()
        a = DjangoApcore.get_instance()
        DjangoApcore._reset_instance()
        b = DjangoApcore.get_instance()
        assert a is not b
        DjangoApcore._reset_instance()


class TestDjangoApcoreServe:
    """Test MCP serving integration."""

    def test_serve_delegates(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        with (
            patch("django_apcore.registry.get_executor") as mock_exec_get,
            patch("django_apcore.management.commands.apcore_serve.serve") as mock_serve,
        ):
            mock_executor = MagicMock()
            mock_exec_get.return_value = mock_executor

            app.serve(
                transport="streamable-http",
                port=9000,
                explorer=True,
            )

            mock_serve.assert_called_once()
            call_kwargs = mock_serve.call_args
            assert call_kwargs[1]["transport"] == "streamable-http"
            assert call_kwargs[1]["port"] == 9000
            assert call_kwargs[1]["explorer"] is True


class TestDjangoApcoreOpenAI:
    """Test OpenAI tools export."""

    def test_to_openai_tools_requires_mcp(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        with (
            patch.dict("sys.modules", {"apcore_mcp": None}),
            pytest.raises(ImportError, match="apcore-mcp"),
        ):
            app.to_openai_tools()

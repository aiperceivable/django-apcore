"""Tests for django_apcore.shortcuts convenience helpers."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Patch targets at the registry module since shortcuts import lazily
_REG = "django_apcore.registry"


class TestExecutorCall:
    """Test the executor_call() shortcut."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @patch(f"{_REG}.get_executor")
    def test_calls_executor_with_module_id_and_inputs(self, mock_get_exec):
        """executor_call() delegates to executor.call()."""
        mock_executor = MagicMock()
        mock_executor.call.return_value = {"result": "ok"}
        mock_get_exec.return_value = mock_executor

        from django_apcore.shortcuts import executor_call

        result = executor_call("my.module", {"key": "value"})

        mock_executor.call.assert_called_once_with(
            "my.module", {"key": "value"}, context=None
        )
        assert result == {"result": "ok"}

    @patch(f"{_REG}.get_context_factory")
    @patch(f"{_REG}.get_executor")
    def test_creates_context_from_request(self, mock_get_exec, mock_get_factory):
        """When request is provided, context is created via factory."""
        mock_executor = MagicMock()
        mock_executor.call.return_value = {}
        mock_get_exec.return_value = mock_executor

        mock_factory = MagicMock()
        mock_context = MagicMock()
        mock_factory.create_context.return_value = mock_context
        mock_get_factory.return_value = mock_factory

        mock_request = MagicMock()

        from django_apcore.shortcuts import executor_call

        executor_call("my.module", request=mock_request)

        mock_factory.create_context.assert_called_once_with(mock_request)
        mock_executor.call.assert_called_once_with(
            "my.module", {}, context=mock_context
        )

    @patch(f"{_REG}.get_context_factory")
    @patch(f"{_REG}.get_executor")
    def test_explicit_context_overrides_request(self, mock_get_exec, mock_get_factory):
        """Explicit context takes precedence over request."""
        mock_executor = MagicMock()
        mock_executor.call.return_value = {}
        mock_get_exec.return_value = mock_executor

        explicit_ctx = MagicMock()
        mock_request = MagicMock()

        from django_apcore.shortcuts import executor_call

        executor_call("my.module", request=mock_request, context=explicit_ctx)

        # Factory should NOT be called
        mock_get_factory.assert_not_called()
        mock_executor.call.assert_called_once_with(
            "my.module", {}, context=explicit_ctx
        )

    @patch(f"{_REG}.get_executor")
    def test_no_request_no_context(self, mock_get_exec):
        """Without request or context, context=None is passed."""
        mock_executor = MagicMock()
        mock_executor.call.return_value = {}
        mock_get_exec.return_value = mock_executor

        from django_apcore.shortcuts import executor_call

        executor_call("my.module")

        mock_executor.call.assert_called_once_with("my.module", {}, context=None)

    @patch(f"{_REG}.get_executor")
    def test_none_inputs_defaults_to_empty_dict(self, mock_get_exec):
        """None inputs are passed as empty dict."""
        mock_executor = MagicMock()
        mock_executor.call.return_value = {}
        mock_get_exec.return_value = mock_executor

        from django_apcore.shortcuts import executor_call

        executor_call("my.module", None)

        mock_executor.call.assert_called_once_with("my.module", {}, context=None)

    @patch(f"{_REG}.get_executor")
    def test_propagates_executor_exceptions(self, mock_get_exec):
        """Executor exceptions propagate to the caller."""
        mock_executor = MagicMock()
        mock_executor.call.side_effect = RuntimeError("module failed")
        mock_get_exec.return_value = mock_executor

        from django_apcore.shortcuts import executor_call

        with pytest.raises(RuntimeError, match="module failed"):
            executor_call("my.module")


class TestExecutorCallAsync:
    """Test the executor_call_async() shortcut."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @patch(f"{_REG}.get_executor")
    def test_async_calls_executor_call_async(self, mock_get_exec):
        """executor_call_async() delegates to executor.call_async()."""
        mock_executor = MagicMock()
        mock_executor.call_async = AsyncMock(return_value={"result": "ok"})
        mock_get_exec.return_value = mock_executor

        from django_apcore.shortcuts import executor_call_async

        result = asyncio.get_event_loop().run_until_complete(
            executor_call_async("my.module", {"key": "value"})
        )

        mock_executor.call_async.assert_called_once_with(
            "my.module", {"key": "value"}, context=None
        )
        assert result == {"result": "ok"}

    @patch(f"{_REG}.get_context_factory")
    @patch(f"{_REG}.get_executor")
    def test_async_creates_context_from_request(self, mock_get_exec, mock_get_factory):
        """Async version creates context from request."""
        mock_executor = MagicMock()
        mock_executor.call_async = AsyncMock(return_value={})
        mock_get_exec.return_value = mock_executor

        mock_factory = MagicMock()
        mock_context = MagicMock()
        mock_factory.create_context.return_value = mock_context
        mock_get_factory.return_value = mock_factory

        mock_request = MagicMock()

        from django_apcore.shortcuts import executor_call_async

        asyncio.get_event_loop().run_until_complete(
            executor_call_async("my.module", request=mock_request)
        )

        mock_factory.create_context.assert_called_once_with(mock_request)
        mock_executor.call_async.assert_called_once_with(
            "my.module", {}, context=mock_context
        )


class TestExecutorStream:
    """Test the executor_stream() shortcut."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @patch(f"{_REG}.get_executor")
    def test_stream_yields_chunks(self, mock_get_exec):
        """executor_stream() yields chunks from executor.stream()."""
        chunks = [{"chunk": 1}, {"chunk": 2}]

        async def mock_stream(module_id, inputs, context=None):
            for c in chunks:
                yield c

        mock_executor = MagicMock()
        mock_executor.stream = mock_stream
        mock_get_exec.return_value = mock_executor

        from django_apcore.shortcuts import executor_stream

        async def collect():
            result = []
            async for chunk in executor_stream("my.module", {"key": "value"}):
                result.append(chunk)
            return result

        result = asyncio.get_event_loop().run_until_complete(collect())
        assert result == chunks

    @patch(f"{_REG}.get_context_factory")
    @patch(f"{_REG}.get_executor")
    def test_stream_creates_context_from_request(self, mock_get_exec, mock_get_factory):
        """Stream version creates context from request."""

        async def mock_stream(module_id, inputs, context=None):
            yield {"done": True}

        mock_executor = MagicMock()
        mock_executor.stream = mock_stream
        mock_get_exec.return_value = mock_executor

        mock_factory = MagicMock()
        mock_context = MagicMock()
        mock_factory.create_context.return_value = mock_context
        mock_get_factory.return_value = mock_factory

        mock_request = MagicMock()

        from django_apcore.shortcuts import executor_stream

        async def collect():
            result = []
            async for chunk in executor_stream("my.module", request=mock_request):
                result.append(chunk)
            return result

        asyncio.get_event_loop().run_until_complete(collect())
        mock_factory.create_context.assert_called_once_with(mock_request)


class TestMCPHelpers:
    """Test MCP helper re-exports."""

    @patch("apcore_mcp.report_progress")
    def test_report_progress_delegates(self, mock_rp):
        """report_progress() delegates to apcore_mcp."""
        mock_rp.return_value = None

        from django_apcore.shortcuts import report_progress

        mock_ctx = MagicMock()
        asyncio.get_event_loop().run_until_complete(
            report_progress(mock_ctx, 0.5, total=1.0, message="half")
        )
        mock_rp.assert_called_once_with(mock_ctx, 0.5, total=1.0, message="half")

    def test_report_progress_noop_without_apcore_mcp(self):
        """report_progress() is a no-op when apcore-mcp is missing."""
        import sys

        from django_apcore.shortcuts import report_progress

        saved = sys.modules.get("apcore_mcp")
        sys.modules["apcore_mcp"] = None  # type: ignore[assignment]
        try:
            # Should not raise
            asyncio.get_event_loop().run_until_complete(
                report_progress(MagicMock(), 1.0)
            )
        finally:
            if saved is not None:
                sys.modules["apcore_mcp"] = saved
            else:
                sys.modules.pop("apcore_mcp", None)

    @patch("apcore_mcp.elicit")
    def test_elicit_delegates(self, mock_el):
        """elicit() delegates to apcore_mcp."""
        mock_el.return_value = {"action": "accept"}

        from django_apcore.shortcuts import elicit

        mock_ctx = MagicMock()
        result = asyncio.get_event_loop().run_until_complete(
            elicit(mock_ctx, "Confirm?")
        )
        mock_el.assert_called_once_with(mock_ctx, "Confirm?", requested_schema=None)
        assert result == {"action": "accept"}

    def test_elicit_returns_none_without_apcore_mcp(self):
        """elicit() returns None when apcore-mcp is missing."""
        import sys

        from django_apcore.shortcuts import elicit

        saved = sys.modules.get("apcore_mcp")
        sys.modules["apcore_mcp"] = None  # type: ignore[assignment]
        try:
            result = asyncio.get_event_loop().run_until_complete(
                elicit(MagicMock(), "Confirm?")
            )
            assert result is None
        finally:
            if saved is not None:
                sys.modules["apcore_mcp"] = saved
            else:
                sys.modules.pop("apcore_mcp", None)

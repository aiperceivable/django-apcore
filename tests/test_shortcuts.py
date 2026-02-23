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

        result = asyncio.run(executor_call_async("my.module", {"key": "value"}))

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

        asyncio.run(executor_call_async("my.module", request=mock_request))

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

        result = asyncio.run(collect())
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

        asyncio.run(collect())
        mock_factory.create_context.assert_called_once_with(mock_request)


class TestMCPHelpers:
    """Test MCP helper re-exports."""

    @patch("apcore_mcp.report_progress")
    def test_report_progress_delegates(self, mock_rp):
        """report_progress() delegates to apcore_mcp."""
        mock_rp.return_value = None

        from django_apcore.shortcuts import report_progress

        mock_ctx = MagicMock()
        asyncio.run(report_progress(mock_ctx, 0.5, total=1.0, message="half"))
        mock_rp.assert_called_once_with(mock_ctx, 0.5, total=1.0, message="half")

    def test_report_progress_noop_without_apcore_mcp(self):
        """report_progress() is a no-op when apcore-mcp is missing."""
        import sys

        from django_apcore.shortcuts import report_progress

        saved = sys.modules.get("apcore_mcp")
        sys.modules["apcore_mcp"] = None  # type: ignore[assignment]
        try:
            # Should not raise
            asyncio.run(report_progress(MagicMock(), 1.0))
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
        result = asyncio.run(elicit(mock_ctx, "Confirm?"))
        mock_el.assert_called_once_with(mock_ctx, "Confirm?", requested_schema=None)
        assert result == {"action": "accept"}

    def test_elicit_returns_none_without_apcore_mcp(self):
        """elicit() returns None when apcore-mcp is missing."""
        import sys

        from django_apcore.shortcuts import elicit

        saved = sys.modules.get("apcore_mcp")
        sys.modules["apcore_mcp"] = None  # type: ignore[assignment]
        try:
            result = asyncio.run(elicit(MagicMock(), "Confirm?"))
            assert result is None
        finally:
            if saved is not None:
                sys.modules["apcore_mcp"] = saved
            else:
                sys.modules.pop("apcore_mcp", None)


class TestCancellableCall:
    """Test cancellable_call shortcut."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @patch("apcore.Context.create")
    @patch(f"{_REG}.get_context_factory")
    @patch(f"{_REG}.get_executor")
    def test_creates_cancel_token(
        self, mock_get_exec, mock_get_factory, mock_ctx_create
    ):
        """cancellable_call() creates a CancelToken and attaches to context."""
        mock_executor = MagicMock()
        mock_executor.call.return_value = {"result": "ok"}
        mock_get_exec.return_value = mock_executor

        mock_ctx = MagicMock()
        mock_ctx_create.return_value = mock_ctx

        from django_apcore.shortcuts import cancellable_call

        result = cancellable_call("test.module", {"key": "value"})

        assert result == {"result": "ok"}
        assert mock_ctx.cancel_token is not None

    @patch("apcore.Context.create")
    @patch(f"{_REG}.get_context_factory")
    @patch(f"{_REG}.get_executor")
    def test_with_timeout(self, mock_get_exec, mock_get_factory, mock_ctx_create):
        """cancellable_call() with timeout still returns result."""
        mock_executor = MagicMock()
        mock_executor.call.return_value = {"ok": True}
        mock_get_exec.return_value = mock_executor

        mock_ctx = MagicMock()
        mock_ctx_create.return_value = mock_ctx

        from django_apcore.shortcuts import cancellable_call

        result = cancellable_call("test.module", timeout=5.0)
        assert result == {"ok": True}

    @patch(f"{_REG}.get_context_factory")
    @patch(f"{_REG}.get_executor")
    def test_uses_request_to_create_context(self, mock_get_exec, mock_get_factory):
        """cancellable_call() creates context from request when provided."""
        mock_executor = MagicMock()
        mock_executor.call.return_value = {"done": True}
        mock_get_exec.return_value = mock_executor

        mock_factory = MagicMock()
        mock_context = MagicMock()
        mock_factory.create_context.return_value = mock_context
        mock_get_factory.return_value = mock_factory

        mock_request = MagicMock()

        from django_apcore.shortcuts import cancellable_call

        result = cancellable_call("test.module", request=mock_request)

        mock_factory.create_context.assert_called_once_with(mock_request)
        assert result == {"done": True}
        assert mock_context.cancel_token is not None

    @patch(f"{_REG}.get_context_factory")
    @patch(f"{_REG}.get_executor")
    def test_explicit_context_used_directly(self, mock_get_exec, mock_get_factory):
        """cancellable_call() uses explicit context without calling factory."""
        mock_executor = MagicMock()
        mock_executor.call.return_value = {"done": True}
        mock_get_exec.return_value = mock_executor

        explicit_ctx = MagicMock()

        from django_apcore.shortcuts import cancellable_call

        cancellable_call("test.module", context=explicit_ctx)

        mock_get_factory.assert_not_called()
        assert explicit_ctx.cancel_token is not None


class TestCancellableCallAsync:
    """Test cancellable_call_async shortcut."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @patch("apcore.Context.create")
    @patch(f"{_REG}.get_context_factory")
    @patch(f"{_REG}.get_executor")
    def test_async_creates_cancel_token(
        self, mock_get_exec, mock_get_factory, mock_ctx_create
    ):
        """cancellable_call_async() creates a CancelToken and attaches."""
        mock_executor = MagicMock()
        mock_executor.call_async = AsyncMock(return_value={"result": "ok"})
        mock_get_exec.return_value = mock_executor

        mock_ctx = MagicMock()
        mock_ctx_create.return_value = mock_ctx

        from django_apcore.shortcuts import cancellable_call_async

        result = asyncio.run(cancellable_call_async("test.module", {"key": "value"}))

        assert result == {"result": "ok"}
        assert mock_ctx.cancel_token is not None

    @patch("apcore.Context.create")
    @patch(f"{_REG}.get_context_factory")
    @patch(f"{_REG}.get_executor")
    def test_async_with_timeout(self, mock_get_exec, mock_get_factory, mock_ctx_create):
        """cancellable_call_async() with timeout still returns result."""
        mock_executor = MagicMock()
        mock_executor.call_async = AsyncMock(return_value={"ok": True})
        mock_get_exec.return_value = mock_executor

        mock_ctx = MagicMock()
        mock_ctx_create.return_value = mock_ctx

        from django_apcore.shortcuts import cancellable_call_async

        result = asyncio.run(cancellable_call_async("test.module", timeout=5.0))
        assert result == {"ok": True}


class TestSubmitTask:
    """Test submit_task shortcut."""

    @patch("django_apcore.tasks.get_task_manager")
    def test_submits_to_task_manager(self, mock_get_tm):
        """submit_task() delegates to task manager's submit()."""
        mock_tm = MagicMock()
        mock_tm.submit = AsyncMock(return_value="task-123")
        mock_get_tm.return_value = mock_tm

        from django_apcore.shortcuts import submit_task

        task_id = asyncio.run(submit_task("test.module", {"key": "value"}))
        assert task_id == "task-123"
        mock_tm.submit.assert_called_once_with(
            "test.module", {"key": "value"}, context=None
        )

    @patch("django_apcore.tasks.get_task_manager")
    def test_none_inputs_defaults_to_empty_dict(self, mock_get_tm):
        """submit_task() passes empty dict when inputs is None."""
        mock_tm = MagicMock()
        mock_tm.submit = AsyncMock(return_value="task-456")
        mock_get_tm.return_value = mock_tm

        from django_apcore.shortcuts import submit_task

        asyncio.run(submit_task("test.module"))
        mock_tm.submit.assert_called_once_with("test.module", {}, context=None)


class TestGetTaskStatus:
    """Test get_task_status shortcut."""

    @patch("django_apcore.tasks.get_task_manager")
    def test_returns_task_info(self, mock_get_tm):
        """get_task_status() returns TaskInfo from task manager."""
        mock_tm = MagicMock()
        mock_info = MagicMock()
        mock_info.status = "completed"
        mock_tm.get_status.return_value = mock_info
        mock_get_tm.return_value = mock_tm

        from django_apcore.shortcuts import get_task_status

        info = get_task_status("task-123")
        assert info.status == "completed"
        mock_tm.get_status.assert_called_once_with("task-123")

    @patch("django_apcore.tasks.get_task_manager")
    def test_returns_none_for_unknown(self, mock_get_tm):
        """get_task_status() returns None for unknown task_id."""
        mock_tm = MagicMock()
        mock_tm.get_status.return_value = None
        mock_get_tm.return_value = mock_tm

        from django_apcore.shortcuts import get_task_status

        info = get_task_status("nonexistent")
        assert info is None


class TestCancelTask:
    """Test cancel_task shortcut."""

    @patch("django_apcore.tasks.get_task_manager")
    def test_cancels_task(self, mock_get_tm):
        """cancel_task() returns True when task is cancelled."""
        mock_tm = MagicMock()
        mock_tm.cancel = AsyncMock(return_value=True)
        mock_get_tm.return_value = mock_tm

        from django_apcore.shortcuts import cancel_task

        result = asyncio.run(cancel_task("task-123"))
        assert result is True
        mock_tm.cancel.assert_called_once_with("task-123")

    @patch("django_apcore.tasks.get_task_manager")
    def test_cancel_returns_false_for_unknown(self, mock_get_tm):
        """cancel_task() returns False for unknown or terminal task."""
        mock_tm = MagicMock()
        mock_tm.cancel = AsyncMock(return_value=False)
        mock_get_tm.return_value = mock_tm

        from django_apcore.shortcuts import cancel_task

        result = asyncio.run(cancel_task("nonexistent"))
        assert result is False

"""Convenience helpers for calling apcore modules from Django views.

Wraps the common pattern of wiring together get_executor(),
get_context_factory(), and Executor.call() into a single function call.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


async def report_progress(
    context: Any,
    progress: float,
    total: float | None = None,
    message: str | None = None,
) -> None:
    """Report execution progress to the MCP client.

    Delegates to ``apcore_mcp.report_progress()``. No-ops silently when
    apcore-mcp is not installed or when called outside an MCP context.
    """
    try:
        from apcore_mcp import report_progress as _report_progress

        await _report_progress(context, progress, total=total, message=message)
    except ImportError:
        pass


async def elicit(
    context: Any,
    message: str,
    requested_schema: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Ask the MCP client for user input via elicitation.

    Delegates to ``apcore_mcp.elicit()``. Returns None when apcore-mcp
    is not installed or when called outside an MCP context.
    """
    try:
        from apcore_mcp import elicit as _elicit

        return await _elicit(context, message, requested_schema=requested_schema)
    except ImportError:
        return None


def executor_call(
    module_id: str,
    inputs: dict[str, Any] | None = None,
    *,
    request: Any = None,
    context: Any = None,
) -> dict:
    """Execute an apcore module synchronously.

    Args:
        module_id: The module identifier to call.
        inputs: Input dict for the module. Defaults to ``{}``.
        request: Optional Django HttpRequest. Used to build a Context
            via the configured ContextFactory when *context* is not given.
        context: Explicit apcore Context. Takes precedence over *request*.

    Returns:
        The module result dict.
    """
    from django_apcore.registry import get_context_factory, get_executor

    executor = get_executor()
    if context is None and request is not None:
        context = get_context_factory().create_context(request)
    return executor.call(module_id, inputs or {}, context=context)


async def executor_call_async(
    module_id: str,
    inputs: dict[str, Any] | None = None,
    *,
    request: Any = None,
    context: Any = None,
) -> dict:
    """Execute an apcore module asynchronously.

    Args:
        module_id: The module identifier to call.
        inputs: Input dict for the module. Defaults to ``{}``.
        request: Optional Django HttpRequest. Used to build a Context
            via the configured ContextFactory when *context* is not given.
        context: Explicit apcore Context. Takes precedence over *request*.

    Returns:
        The module result dict.
    """
    from django_apcore.registry import get_context_factory, get_executor

    executor = get_executor()
    if context is None and request is not None:
        context = get_context_factory().create_context(request)
    return await executor.call_async(module_id, inputs or {}, context=context)


async def executor_stream(
    module_id: str,
    inputs: dict[str, Any] | None = None,
    *,
    request: Any = None,
    context: Any = None,
) -> AsyncIterator[dict[str, Any]]:
    """Stream an apcore module's output asynchronously.

    Args:
        module_id: The module identifier to call.
        inputs: Input dict for the module. Defaults to ``{}``.
        request: Optional Django HttpRequest. Used to build a Context
            via the configured ContextFactory when *context* is not given.
        context: Explicit apcore Context. Takes precedence over *request*.

    Yields:
        Chunk dicts from the streaming module.
    """
    from django_apcore.registry import get_context_factory, get_executor

    executor = get_executor()
    if context is None and request is not None:
        context = get_context_factory().create_context(request)
    async for chunk in executor.stream(module_id, inputs or {}, context=context):
        yield chunk


def cancellable_call(
    module_id: str,
    inputs: dict[str, Any] | None = None,
    *,
    request: Any = None,
    context: Any = None,
    timeout: float | None = None,
) -> dict:
    """Execute an apcore module with CancelToken.

    Creates a CancelToken and attaches it to the context.
    If timeout is provided (seconds), auto-cancels after that duration.

    Args:
        module_id: The module identifier to call.
        inputs: Input dict for the module. Defaults to ``{}``.
        request: Optional Django HttpRequest. Used to build a Context
            via the configured ContextFactory when *context* is not given.
        context: Explicit apcore Context. Takes precedence over *request*.
        timeout: Optional timeout in seconds. If provided, the CancelToken
            is automatically cancelled after the specified duration.

    Returns:
        The module result dict.
    """
    from apcore import CancelToken, Context

    from django_apcore.registry import get_context_factory, get_executor

    executor = get_executor()
    token = CancelToken()

    if context is None:
        if request is not None:
            context = get_context_factory().create_context(request)
        else:
            context = Context.create()
    context.cancel_token = token

    if timeout is not None:
        import threading

        timer = threading.Timer(timeout, token.cancel)
        timer.start()
        try:
            return executor.call(module_id, inputs or {}, context=context)
        finally:
            timer.cancel()

    return executor.call(module_id, inputs or {}, context=context)


async def cancellable_call_async(
    module_id: str,
    inputs: dict[str, Any] | None = None,
    *,
    request: Any = None,
    context: Any = None,
    timeout: float | None = None,
) -> dict:
    """Execute an apcore module asynchronously with CancelToken.

    Creates a CancelToken and attaches it to the context.
    If timeout is provided (seconds), auto-cancels after that duration.

    Args:
        module_id: The module identifier to call.
        inputs: Input dict for the module. Defaults to ``{}``.
        request: Optional Django HttpRequest. Used to build a Context
            via the configured ContextFactory when *context* is not given.
        context: Explicit apcore Context. Takes precedence over *request*.
        timeout: Optional timeout in seconds. If provided, the CancelToken
            is automatically cancelled after the specified duration.

    Returns:
        The module result dict.
    """
    import asyncio

    from apcore import CancelToken, Context

    from django_apcore.registry import get_context_factory, get_executor

    executor = get_executor()
    token = CancelToken()

    if context is None:
        if request is not None:
            context = get_context_factory().create_context(request)
        else:
            context = Context.create()
    context.cancel_token = token

    if timeout is not None:

        async def _cancel_after_timeout() -> None:
            await asyncio.sleep(timeout)
            token.cancel()

        cancel_task = asyncio.create_task(_cancel_after_timeout())
        try:
            return await executor.call_async(module_id, inputs or {}, context=context)
        finally:
            cancel_task.cancel()

    return await executor.call_async(module_id, inputs or {}, context=context)


async def submit_task(
    module_id: str,
    inputs: dict[str, Any] | None = None,
    *,
    context: Any = None,
) -> str:
    """Submit an async task to the AsyncTaskManager.

    Args:
        module_id: The module identifier to submit.
        inputs: Input dict for the module. Defaults to ``{}``.
        context: Explicit apcore Context.

    Returns:
        A task_id string identifying the submitted task.
    """
    from django_apcore.tasks import get_task_manager

    tm = get_task_manager()
    return await tm.submit(module_id, inputs or {}, context=context)


def get_task_status(task_id: str) -> Any:
    """Query task status from the AsyncTaskManager.

    Args:
        task_id: The identifier of the task to query.

    Returns:
        TaskInfo or None if the task is not found.
    """
    from django_apcore.tasks import get_task_manager

    return get_task_manager().get_status(task_id)


async def cancel_task(task_id: str) -> bool:
    """Cancel a running async task.

    Args:
        task_id: The identifier of the task to cancel.

    Returns:
        True if cancelled, False if not found or already terminal.
    """
    from django_apcore.tasks import get_task_manager

    return await get_task_manager().cancel(task_id)

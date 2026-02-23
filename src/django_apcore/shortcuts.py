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

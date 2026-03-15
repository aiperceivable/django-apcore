"""DjangoApcore: Unified entry point for django-apcore.

Consolidates Registry, Executor, ContextFactory, TaskManager, and MCP
serving into a single class with a Django-aware API. Follows the same
pattern as ``apcore.APCore`` and ``apcore_mcp.APCoreMCP``.

Usage::

    from django_apcore import DjangoApcore

    app = DjangoApcore()

    # Call a module from a Django view
    result = app.call("users.list", {"page": 1}, request=request)

    # Async call
    result = await app.call_async("users.list", {"page": 1}, request=request)

    # Stream
    async for chunk in app.stream("ai.chat", {"prompt": "hello"}, request=request):
        ...

    # Register a module
    @app.module(id="math.add")
    def add(a: int, b: int) -> int:
        return a + b

    # Scan endpoints
    modules = app.scan(source="ninja")

    # Start MCP server
    app.serve(transport="streamable-http", port=9090, explorer=True)

    # Export OpenAI tools
    tools = app.to_openai_tools()
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

logger = logging.getLogger("django_apcore")

_instance: DjangoApcore | None = None
_instance_lock = threading.Lock()


class DjangoApcore:
    """Unified entry point for django-apcore.

    Provides a single object to access all django-apcore functionality:
    Registry, Executor, context mapping, task management, scanning,
    MCP serving, and OpenAI export.

    All singletons from ``django_apcore.registry`` are lazily accessed
    via properties, so this class integrates seamlessly with Django's
    app lifecycle.
    """

    def __init__(self) -> None:
        """Create a DjangoApcore instance.

        Configuration is read from Django's ``APCORE_*`` settings.
        No arguments needed — everything is resolved from settings.
        """

    # ------------------------------------------------------------------
    # Properties — lazy access to singletons
    # ------------------------------------------------------------------

    @property
    def registry(self) -> Any:
        """The apcore Registry singleton."""
        from django_apcore.registry import get_registry

        return get_registry()

    @property
    def executor(self) -> Any:
        """The apcore Executor singleton (with extensions applied)."""
        from django_apcore.registry import get_executor

        return get_executor()

    @property
    def extension_manager(self) -> Any:
        """The ExtensionManager singleton."""
        from django_apcore.registry import get_extension_manager

        return get_extension_manager()

    @property
    def context_factory(self) -> Any:
        """The ContextFactory singleton for Django request → apcore Context."""
        from django_apcore.registry import get_context_factory

        return get_context_factory()

    @property
    def metrics_collector(self) -> Any | None:
        """The MetricsCollector singleton, or None if metrics are disabled."""
        from django_apcore.registry import get_metrics_collector

        return get_metrics_collector()

    @property
    def task_manager(self) -> Any:
        """The AsyncTaskManager singleton."""
        from django_apcore.tasks import get_task_manager

        return get_task_manager()

    @property
    def settings(self) -> Any:
        """The validated ApcoreSettings dataclass."""
        from django_apcore.settings import get_apcore_settings

        return get_apcore_settings()

    # ------------------------------------------------------------------
    # Context helpers
    # ------------------------------------------------------------------

    def _resolve_context(
        self,
        request: Any = None,
        context: Any = None,
    ) -> Any:
        """Build an apcore Context from a Django request or explicit context.

        Args:
            request: Optional Django HttpRequest.
            context: Explicit apcore Context (takes precedence).

        Returns:
            An apcore Context, or None if neither is provided.
        """
        if context is not None:
            return context
        if request is not None:
            return self.context_factory.create_context(request)
        return None

    # ------------------------------------------------------------------
    # Module execution
    # ------------------------------------------------------------------

    def call(
        self,
        module_id: str,
        inputs: dict[str, Any] | None = None,
        *,
        request: Any = None,
        context: Any = None,
    ) -> dict[str, Any]:
        """Execute a module synchronously.

        Args:
            module_id: The module identifier to call.
            inputs: Input dict for the module.
            request: Optional Django HttpRequest (auto-builds context).
            context: Explicit apcore Context (takes precedence over request).

        Returns:
            The module result dict.
        """
        ctx = self._resolve_context(request, context)
        return self.executor.call(module_id, inputs or {}, context=ctx)

    async def call_async(
        self,
        module_id: str,
        inputs: dict[str, Any] | None = None,
        *,
        request: Any = None,
        context: Any = None,
    ) -> dict[str, Any]:
        """Execute a module asynchronously.

        Args:
            module_id: The module identifier to call.
            inputs: Input dict for the module.
            request: Optional Django HttpRequest (auto-builds context).
            context: Explicit apcore Context (takes precedence over request).

        Returns:
            The module result dict.
        """
        ctx = self._resolve_context(request, context)
        return await self.executor.call_async(module_id, inputs or {}, context=ctx)

    async def stream(
        self,
        module_id: str,
        inputs: dict[str, Any] | None = None,
        *,
        request: Any = None,
        context: Any = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream a module's output asynchronously.

        Args:
            module_id: The module identifier to stream.
            inputs: Input dict for the module.
            request: Optional Django HttpRequest (auto-builds context).
            context: Explicit apcore Context (takes precedence over request).

        Yields:
            Chunk dicts from the streaming module.
        """
        ctx = self._resolve_context(request, context)
        async for chunk in self.executor.stream(module_id, inputs or {}, context=ctx):
            yield chunk

    def cancellable_call(
        self,
        module_id: str,
        inputs: dict[str, Any] | None = None,
        *,
        request: Any = None,
        context: Any = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Execute a module with cooperative cancellation.

        Creates a CancelToken and optionally auto-cancels after timeout.

        Args:
            module_id: The module identifier to call.
            inputs: Input dict for the module.
            request: Optional Django HttpRequest.
            context: Explicit apcore Context.
            timeout: Timeout in seconds. Falls back to
                     APCORE_CANCEL_DEFAULT_TIMEOUT setting.

        Returns:
            The module result dict.
        """
        from django_apcore.shortcuts import cancellable_call

        return cancellable_call(
            module_id,
            inputs,
            request=request,
            context=context,
            timeout=timeout,
        )

    async def cancellable_call_async(
        self,
        module_id: str,
        inputs: dict[str, Any] | None = None,
        *,
        request: Any = None,
        context: Any = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Execute a module asynchronously with cooperative cancellation.

        Args:
            module_id: The module identifier to call.
            inputs: Input dict for the module.
            request: Optional Django HttpRequest.
            context: Explicit apcore Context.
            timeout: Timeout in seconds.

        Returns:
            The module result dict.
        """
        from django_apcore.shortcuts import cancellable_call_async

        return await cancellable_call_async(
            module_id,
            inputs,
            request=request,
            context=context,
            timeout=timeout,
        )

    # ------------------------------------------------------------------
    # Module registration
    # ------------------------------------------------------------------

    def module(
        self,
        id: str | None = None,  # noqa: A002
        description: str | None = None,
        tags: list[str] | None = None,
        version: str = "1.0.0",
        **kwargs: Any,
    ) -> Callable:
        """Decorator to register a function as an apcore module.

        Usage::

            @app.module(id="math.add", tags=["math"])
            def add(a: int, b: int) -> int:
                return a + b

        Args:
            id: Module identifier. Defaults to function's qualified name.
            description: Human-readable description.
            tags: Categorization tags.
            version: Module version string.
            **kwargs: Additional arguments passed to ``apcore.module()``.

        Returns:
            Decorator function.
        """
        from apcore import module as apcore_module

        def decorator(func: Callable) -> Callable:
            inner = apcore_module(
                id=id,
                description=description,
                tags=tags,
                version=version,
                registry=self.registry,
                **kwargs,
            )
            return inner(func)

        return decorator

    def register(self, module_id: str, module_obj: Any) -> None:
        """Register a module object directly.

        Args:
            module_id: The ID to register the module under.
            module_obj: The module instance.
        """
        self.registry.register(module_id, module_obj)

    def list_modules(
        self,
        tags: list[str] | None = None,
        prefix: str | None = None,
    ) -> list[str]:
        """List registered module IDs, optionally filtered.

        Args:
            tags: Only include modules with all specified tags.
            prefix: Only include modules whose ID starts with this prefix.

        Returns:
            Sorted list of module ID strings.
        """
        return self.registry.list(tags=tags, prefix=prefix)

    def describe(self, module_id: str) -> str:
        """Get a module's description (for AI/LLM use).

        Args:
            module_id: The module to describe.

        Returns:
            Human-readable description.
        """
        return self.registry.describe(module_id)

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    async def submit_task(
        self,
        module_id: str,
        inputs: dict[str, Any] | None = None,
        *,
        context: Any = None,
    ) -> str:
        """Submit an async task.

        Args:
            module_id: The module identifier to submit.
            inputs: Input dict for the module.
            context: Explicit apcore Context.

        Returns:
            A task_id string.
        """
        return await self.task_manager.submit(
            module_id,
            inputs or {},
            context=context,
        )

    def get_task_status(self, task_id: str) -> Any:
        """Query task status.

        Args:
            task_id: The task identifier.

        Returns:
            TaskInfo or None.
        """
        return self.task_manager.get_status(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task.

        Args:
            task_id: The task identifier.

        Returns:
            True if cancelled, False otherwise.
        """
        return await self.task_manager.cancel(task_id)

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    def scan(
        self,
        source: str = "ninja",
        *,
        include: str | None = None,
        exclude: str | None = None,
    ) -> list[Any]:
        """Scan Django API endpoints and return ScannedModule instances.

        Args:
            source: Scanner source ('ninja' or 'drf').
            include: Regex pattern to include.
            exclude: Regex pattern to exclude.

        Returns:
            List of ScannedModule instances.
        """
        from django_apcore.scanners import get_scanner

        scanner = get_scanner(source)
        return scanner.scan(include=include, exclude=exclude)

    # ------------------------------------------------------------------
    # MCP serving
    # ------------------------------------------------------------------

    def serve(
        self,
        *,
        transport: str | None = None,
        host: str | None = None,
        port: int | None = None,
        name: str | None = None,
        explorer: bool | None = None,
        explorer_prefix: str | None = None,
        allow_execute: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Start an MCP server with registered modules.

        All arguments are optional — defaults come from Django settings.

        Args:
            transport: 'stdio', 'streamable-http', or 'sse'.
            host: Host address for HTTP transports.
            port: Port number for HTTP transports.
            name: MCP server name.
            explorer: Enable Tool Explorer UI.
            explorer_prefix: URL prefix for explorer.
            allow_execute: Allow execution from explorer.
            **kwargs: Additional arguments passed to apcore_mcp.serve().
        """
        from django_apcore.management.commands.apcore_serve import serve

        s = self.settings
        serve(
            self.executor,
            transport=transport or s.serve_transport,
            host=host or s.serve_host,
            port=port if port is not None else s.serve_port,
            name=name or s.server_name,
            explorer=explorer if explorer is not None else s.explorer_enabled,
            explorer_prefix=(
                explorer_prefix if explorer_prefix is not None else s.explorer_prefix
            ),
            allow_execute=(
                allow_execute if allow_execute is not None else s.explorer_allow_execute
            ),
            **kwargs,
        )

    def to_openai_tools(
        self,
        *,
        tags: list[str] | None = None,
        prefix: str | None = None,
        embed_annotations: bool = False,
        strict: bool = False,
    ) -> list[dict[str, Any]]:
        """Export modules as OpenAI-compatible tool definitions.

        Args:
            tags: Filter modules by tags.
            prefix: Filter modules by ID prefix.
            embed_annotations: Include annotation metadata in descriptions.
            strict: Add strict: true for Structured Outputs.

        Returns:
            List of OpenAI tool definition dicts.
        """
        try:
            from apcore_mcp import to_openai_tools
        except ImportError:
            raise ImportError(
                "apcore-mcp is required for to_openai_tools(). "
                "Install with: pip install django-apcore[mcp]"
            ) from None

        return to_openai_tools(
            self.registry,
            tags=tags,
            prefix=prefix,
            embed_annotations=embed_annotations,
            strict=strict,
        )

    # ------------------------------------------------------------------
    # MCP helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def report_progress(
        context: Any,
        progress: float,
        total: float | None = None,
        message: str | None = None,
    ) -> None:
        """Report execution progress to an MCP client.

        No-ops silently when apcore-mcp is not installed.
        """
        from django_apcore.shortcuts import report_progress

        await report_progress(context, progress, total=total, message=message)

    @staticmethod
    async def elicit(
        context: Any,
        message: str,
        requested_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Ask the MCP client for user input via elicitation.

        Returns None when apcore-mcp is not installed.
        """
        from django_apcore.shortcuts import elicit

        return await elicit(
            context,
            message,
            requested_schema=requested_schema,
        )

    # ------------------------------------------------------------------
    # Singleton access
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> DjangoApcore:
        """Return the process-wide singleton DjangoApcore instance.

        Creates the instance on first call. Thread-safe.

        Returns:
            The shared DjangoApcore instance.
        """
        global _instance
        if _instance is None:
            with _instance_lock:
                if _instance is None:
                    _instance = cls()
        return _instance

    @classmethod
    def _reset_instance(cls) -> None:
        """Reset the singleton. For testing only."""
        global _instance
        with _instance_lock:
            _instance = None

# Upstream SDK Analysis: apcore / apcore-python / apcore-mcp-python

> **Date**: 2026-02-23 (updated from 2026-02-20)
> **Context**: Findings from building django-apcore v0.2.0, updated for v0.1.0 redesign targeting apcore v0.6.0 and apcore-mcp v0.4.0.
> **Scope**: Maps the full upstream API surface, identifies what django-apcore uses, and documents new capabilities for integration.

---

## 1. Upstream Version Summary

| Library | Previous (django-apcore v0.2.0) | Current (django-apcore v0.1.0) | Key Changes |
|---------|--------------------------------|-------------------------------|-------------|
| **apcore** | v0.5.0 | v0.6.0 | Extension System, AsyncTaskManager, CancelToken, W3C TraceContext, Registry hooks, streaming annotations |
| **apcore-mcp** | v0.1.0 | v0.4.0 | Requires apcore>=0.6.0, Prometheus metrics, trace_id passback, input validation |

---

## 2. apcore v0.6.0 — Full API Surface

### 2.1 New in v0.6.0

| Component | API | django-apcore v0.1.0 Usage |
|-----------|-----|---------------------------|
| **ExtensionManager** | `ExtensionManager()`, `.register(point, ext)`, `.get(point)`, `.get_all(point)`, `.apply(registry, executor)`, `.list_points()` | Core composition mechanism — `setup_extensions()` builds and applies |
| **ExtensionPoint** | 5 built-in: discoverer, middleware, acl, span_exporter, module_validator | All 5 used via Django settings |
| **AsyncTaskManager** | `AsyncTaskManager(executor, max_concurrent=, max_tasks=)`, `.submit()`, `.get_status()`, `.cancel()`, `.shutdown()`, `.list_tasks()`, `.cleanup()` | `get_task_manager()` singleton, `apcore_tasks` command, `submit_task()` / `cancel_task()` shortcuts |
| **CancelToken** | `CancelToken()`, `.cancel()`, `.check()`, `.is_cancelled`, `.reset()` | `cancellable_call()` / `cancellable_call_async()` shortcuts |
| **ExecutionCancelledError** | Exception raised on `.check()` when cancelled | Propagated through shortcuts |
| **TraceContext** | `TraceContext.inject(ctx)`, `.extract(headers)`, `.from_traceparent(str)` | `DjangoContextFactory` extracts traceparent from HTTP headers |
| **TraceParent** | `TraceParent(version, trace_id, parent_id, trace_flags)` | Passed to `Context.create(trace_parent=)` |
| **Registry.set_discoverer()** | Custom discovery hook | Set via `ExtensionManager.apply()` |
| **Registry.set_validator()** | Custom validation hook | Set via `ExtensionManager.apply()` |
| **Registry.describe()** | Human-readable module description | Available through Registry singleton |
| **Registry.watch() / unwatch()** | Hot-reload file watching | `APCORE_HOT_RELOAD` / `APCORE_HOT_RELOAD_PATHS` settings |
| **ModuleAnnotations.streaming** | `streaming: bool = False` | Passed through scanner/writer pipeline |
| **ModuleExecuteError** | New error type | Handled in error paths |
| **InternalError** | New error type | Handled in error paths |
| **ErrorCodes** | Pre-defined error code constants | Used for error categorization |
| **Discoverer protocol** | `discover(roots: list[str]) -> list[dict]` | `DjangoDiscoverer` implements |
| **ModuleValidator protocol** | `validate(module) -> list[str]` | `DjangoModuleValidator` implements |
| **Identity.roles** | Changed: `list[str]` → `tuple[str, ...]` | `DjangoContextFactory` updated |

### 2.2 Existing API (Continued Usage)

| Component | Used by django-apcore v0.1.0 |
|-----------|------------------------------|
| **Registry** | `Registry(config=)`, `.register()`, `.count`, `.on()`, `.discover()`, `.module_ids`, `.get_definition()`, `.has()`, `.list()` |
| **BindingLoader** | `.load_binding_dir(dir, registry, pattern=)` — via DjangoDiscoverer |
| **@module decorator** | `id`, `description`, `tags`, `version`, `annotations`, `metadata` |
| **Executor** | `Executor(registry, middlewares=, acl=, config=)`, `.call()`, `.call_async()`, `.stream()`, `.validate()`, `.use()` |
| **Context** | `Context.create(identity=, trace_parent=, data=)`, `.child()`, `.cancel_token` |
| **Identity** | `Identity(id=, type=, roles=, attrs=)` — roles now tuple |
| **ContextFactory** | Protocol implemented by `DjangoContextFactory` |
| **ACL** | `ACL.load(path)` via settings |
| **Config** | `Config(data)` via settings |
| **Middleware system** | `Middleware`, `LoggingMiddleware`, `TracingMiddleware`, `MetricsMiddleware`, `ObsLoggingMiddleware` |
| **Observability** | `Span`, `StdoutExporter`, `InMemoryExporter`, `OTLPExporter`, `ContextLogger`, `MetricsCollector` |

### 2.3 Not Used by django-apcore

| Component | Reason |
|-----------|--------|
| `Registry.unregister()` | No dynamic deregistration use case |
| `Registry.clear_cache()` | Managed by hot-reload system |
| `Executor.use_before() / use_after()` | Extension-style middleware registration preferred |
| `Executor.remove()` | No dynamic middleware removal use case |
| `ModuleExample` | No scanner-generated examples |
| `DependencyInfo` | No inter-module dependency tracking |
| `DiscoveredModule` | DjangoDiscoverer returns raw dicts per protocol |
| `ACLRule` (programmatic) | ACL loaded from YAML only |
| `MiddlewareChainError` | Caught internally by Executor |
| `BeforeMiddleware / AfterMiddleware` | Full Middleware class preferred |

---

## 3. apcore-mcp v0.4.0 — Full API Surface

### 3.1 Changes from v0.1.0

| Component | Change | django-apcore v0.1.0 Usage |
|-----------|--------|---------------------------|
| **Dependency** | Requires apcore>=0.6.0 (was >=0.5.0) | Aligned |
| **serve()** | `metrics_collector=`, `validate_inputs=`, `tags=`, `prefix=`, `log_level=` params | Exposed via settings + CLI args |
| **MCPServer** | `metrics_collector=`, `validate_inputs=`, `tags=`, `prefix=` params | Embedded server support |
| **MetricsExporter** | Protocol for Prometheus metrics | `MetricsCollector` implements it |

### 3.2 Full API Usage

| Component | Used by django-apcore v0.1.0 |
|-----------|------------------------------|
| **serve()** | Full API: transport, host, port, name, version, on_startup, on_shutdown, tags, prefix, log_level, validate_inputs, metrics_collector |
| **to_openai_tools()** | Full API: embed_annotations, strict, tags, prefix |
| **MCPServer** | `.start()`, `.stop()`, `.wait()`, `.address` — for embedded server |
| **report_progress()** | Via `shortcuts.report_progress()` |
| **elicit()** | Via `shortcuts.elicit()` |
| **MCP_PROGRESS_KEY / MCP_ELICIT_KEY** | Context.data injection keys |

### 3.3 Not Used by django-apcore

| Component | Reason |
|-----------|--------|
| **MCPServerFactory** | Internal to serve() / MCPServer |
| **ExecutionRouter** | Internal to serve() / MCPServer |
| **RegistryListener** | Internal dynamic tool sync |
| **TransportManager** | Internal transport lifecycle |
| **SchemaConverter** | Internal schema conversion |
| **AnnotationMapper** | Internal annotation mapping |
| **ErrorMapper** | Internal error sanitization |
| **ModuleIDNormalizer** | Internal ID conversion |
| **OpenAIConverter** | Internal to to_openai_tools() |

---

## 4. Integration Status

All P0, P1, and P2 items from previous analysis are resolved. The v0.1.0 redesign adds:

| Integration | Status | Mechanism |
|-------------|--------|-----------|
| Extension System | **New** | `setup_extensions()` → `ExtensionManager.apply()` |
| AsyncTaskManager | **New** | `get_task_manager()` + `apcore_tasks` command |
| CancelToken | **New** | `cancellable_call()` / `cancellable_call_async()` |
| W3C TraceContext | **New** | `DjangoContextFactory` extracts traceparent header |
| Registry Discoverer | **New** | `DjangoDiscoverer` implements `Discoverer` protocol |
| Registry Validator | **New** | `DjangoModuleValidator` implements `ModuleValidator` protocol |
| Hot-Reload | **New** | `APCORE_HOT_RELOAD` + `APCORE_HOT_RELOAD_PATHS` settings |
| Prometheus Metrics | **New** | `APCORE_SERVE_METRICS` setting → serve(metrics_collector=) |
| Module Filtering | **New** | `APCORE_SERVE_TAGS` / `APCORE_SERVE_PREFIX` settings |
| Identity.roles tuple | **Migration** | DjangoContextFactory returns tuple (transparent) |
| Streaming annotations | **Passthrough** | ModuleAnnotations.streaming flows through scanner/writer |

---

## 5. Remaining Gaps

None. django-apcore v0.1.0 provides full integration with all public API surfaces of apcore v0.6.0 and apcore-mcp v0.4.0.

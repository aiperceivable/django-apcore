# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-23

Initial public release of django-apcore — a Django app that bridges the apcore protocol to Django, enabling existing REST APIs to be served as MCP tools for AI agents.

### Core

- Django `AppConfig` with Extension-First startup flow
- `Registry` and `Executor` singletons via `ExtensionManager.apply()` auto-assembly
- `ExtensionManager` integration with 5 extension points: discoverer, middleware, acl, span_exporter, module_validator
- `DjangoDiscoverer` — discovers modules from YAML bindings and `@module`-decorated functions in `INSTALLED_APPS`
- `DjangoModuleValidator` — validates module IDs against reserved words and length limits
- Auto-discovery of apcore modules on Django startup

### Management Commands

- `apcore_serve` — start MCP server (stdio/streamable-http/sse) with metrics, input validation, and tag/prefix filtering
- `apcore_scan` — scan django-ninja and DRF endpoints to generate apcore module definitions
- `apcore_export` — export registered modules as OpenAI-compatible tool definitions
- `apcore_tasks` — list, cancel, and clean up async tasks

### Scanners

- `NinjaScanner` — scans django-ninja APIs via Pydantic schemas
- `DRFScanner` — scans DRF APIs via drf-spectacular OpenAPI generation
- Include/exclude pattern filtering for endpoint selection
- Deduplication of scanned modules

### Output Writers

- `YAMLWriter` — generates `*.binding.yaml` module definition files
- `PythonWriter` — generates Python module files with `@module` decorators
- Dry-run mode for previewing output without writing files

### Shortcuts

- `executor_call` / `executor_call_async` — sync and async module execution
- `executor_stream` — streaming module execution
- `cancellable_call` / `cancellable_call_async` — execution with `CancelToken` and optional timeout
- `submit_task` / `get_task_status` / `cancel_task` — async task management
- `report_progress` — MCP progress reporting
- `elicit` — MCP user input elicitation

### Django Context

- `DjangoContextFactory` — creates apcore `Context` from Django `HttpRequest`
- `Identity` mapping from `request.user` with group-based roles (as `tuple`)
- W3C TraceContext extraction from `traceparent` HTTP header

### Observability

- Configurable logging via `APCORE_OBSERVABILITY_LOGGING`
- Tracing with pluggable span exporters (stdout, in-memory, OTLP)
- `MetricsCollector` integration for Prometheus `/metrics` endpoint
- Sampling strategies configurable via `APCORE_TRACING`

### Middleware & ACL

- Pluggable middleware pipeline via `APCORE_MIDDLEWARES` setting
- YAML-based ACL loaded from `APCORE_ACL_PATH`
- Middleware and ACL registered as apcore extensions

### Embedded Server

- Optional embedded MCP server started alongside Django via `APCORE_EMBEDDED_SERVER`
- Non-blocking startup with configurable transport and host/port

### Configuration

- 30+ `APCORE_*` Django settings with type validation and sensible defaults
- Settings include: module discovery, server transport, middleware pipeline, ACL, tracing, metrics, task management, hot-reload, embedded server, and module filtering

### Example Project

- Docker Compose demo with web + MCP services
- Sample apcore modules (hello, math_tools, slow_task)
- Integration test suite for the example project

### Testing

- 393 tests across 20 test files
- Unit tests for all components (settings, extensions, context, registry, shortcuts, tasks, scanners, writers, commands)
- Integration tests for the full Extension-First pipeline
- Async test support via pytest-asyncio

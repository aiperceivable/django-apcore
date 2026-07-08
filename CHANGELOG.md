# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-07-08

Restores reachable approval/ACL governance for scanned routes, adds apcore-cli integration
(`create_cli`) and a runnable ACL demo — bringing django-apcore to feature parity with
fastapi-apcore. All 526 tests pass.

### Added
- **`DjangoApcore.create_cli(...)`** — turns your scanned Django routes (via the `ninja` / `drf`
  scanners) into an [apcore-cli](https://github.com/aiperceivable/apcore-cli) Click CLI whose
  commands proxy to the running Django server (`list` / `describe` + one command per route). New
  `[cli]` extra (`apcore-cli>=0.10.3`, `click>=8.0`). Covered by `tests/test_create_cli.py`.
- **ACL demo (`examples/acl_demo/`)** — a runnable Django project demonstrating apcore ACL
  enforcement on module calls: an `acl.yaml` (admins may call anything; `orders.list` public; else
  denied), views that map `ACLDeniedError` → HTTP 403, and an `X-Roles` demo auth shortcut mapped
  to an apcore `Identity` via `DjangoContextFactory`. Run with
  `python examples/acl_demo/manage.py runserver`; covered end-to-end by `tests/test_acl_demo.py`.
- Conformance regression test running the shared `apcore_toolkit.conformance` verifier against
  `DjangoRegistryWriter` (`tests/test_registry_writer.py::TestAnnotationConformance`).

### Fixed
- **Behavioral annotations were dropped during registration** (fixes #1). `DjangoRegistryWriter`
  overrode `_to_function_module` and built `FunctionModule` without forwarding `annotations`,
  so every `registry.get_definition(...).annotations` was `None` and approval/ACL gating that
  keys on `requires_approval` **silently never fired for scanned Django routes**. The writer no
  longer overrides `_to_function_module`; it overrides only the toolkit base writer's narrow
  hooks — `_adapt_func` (strips the leading `request` param) and `_build_input_schema` /
  `_build_output_schema` (explicit schema models) — and inherits the centralized, all-fields
  `_build_function_module`, so annotations can no longer be dropped. `write` also now threads
  `allowed_prefixes`.

### Changed
- Dependency floor raised: `apcore-toolkit >= 0.10.0` — provides the centralized `RegistryWriter`
  hooks (`_adapt_func` / `_build_input_schema` / `_build_output_schema`) and the shared
  `apcore_toolkit.conformance` verifier.
- Dependency floor raised: `apcore-mcp >= 0.17.1` (in the `mcp` / `all` extras) — the
  apcore-toolkit 0.10.0-compatible patch.

## [0.4.0] - 2026-06-30

### Changed
- **Bumped SDK floors** to `apcore>=0.25.0`, `apcore-toolkit>=0.9.0`, and
  `apcore-mcp>=0.17.0` (in the `mcp`/`all` extras). This release of the
  ecosystem fixes all three defects reported under 0.4.0 (see *SDK notes*),
  so the corresponding downstream workarounds have been removed.

### Fixed
- **NinjaScanner module IDs no longer leak the django-ninja namespace.**
  django-ninja >= 1.5 auto-generates operationIds as `{namespace}_{func_name}`
  (e.g. `demo_api_list_tasks`). The scanner derived the action verb from the
  operationId's *first* underscore segment, so every CRUD endpoint collapsed
  onto `api.tasks.demo` (then `_2`…`_5` after de-duplication) instead of
  `api.tasks.list` / `create` / `get` / `update` / `delete`. The verb is now
  taken from the resolved view function name (`list_tasks` → `list`), which is
  the reliable source. The example bindings have been regenerated accordingly.

### Added
- **Embedded MCP server now has full pipeline / Explorer parity.** apcore-mcp
  0.17.0 adds the formatting, pipeline and Explorer parameters to the
  non-blocking `MCPServer` class, so the embedded server (`APCORE_EMBEDDED_SERVER`)
  now honours the same settings the `apcore_serve` command already did:
  - `APCORE_OUTPUT_FORMATTER` — resolved and passed through (previously ignored
    with a warning because `MCPServer` rejected it).
  - `APCORE_SERVE_OUTPUT_FORMAT`, `APCORE_SERVE_STRATEGY`,
    `APCORE_SERVE_OBSERVABILITY`, `APCORE_SERVE_REDACT_OUTPUT`,
    `APCORE_SERVE_TRACE` — pipeline / observability controls.
  - `APCORE_EXPLORER_ENABLED`, `APCORE_EXPLORER_PREFIX`,
    `APCORE_EXPLORER_ALLOW_EXECUTE`, `APCORE_EXPLORER_TITLE`,
    `APCORE_EXPLORER_PROJECT_NAME`, `APCORE_EXPLORER_PROJECT_URL` — Tool Explorer
    UI and branding for HTTP transports.

### Removed
- **`extensions.py` import fallback.** apcore 0.25.0 restored
  `MAX_MODULE_ID_LENGTH` / `RESERVED_WORDS` to the package root, so the
  `try/except` fallback to `apcore.registry.registry` is gone — back to a plain
  `from apcore import ...`.
- **`NinjaScanner._normalize_response_keys` workaround.** apcore-toolkit 0.9.0
  coerces OpenAPI response keys to strings before matching, so django-ninja's
  integer status-code keys no longer crash `extract_output_schema`. The
  end-to-end regression test (`test_integer_response_status_keys`) is retained.

### SDK notes (previously-reported defects — now fixed upstream)
- ✅ `apcore` 0.25.0 restored `MAX_MODULE_ID_LENGTH` / `RESERVED_WORDS` to the
  package root (`apcore.__all__`).
- ✅ `apcore-mcp` 0.17.0 gives the non-blocking `MCPServer` the same
  `output_formatter` / `output_format` / `strategy` / `observability` /
  `redact_output` / `trace` / explorer-branding parameters as the blocking
  `serve()` API, removing the asymmetry that blocked embedded serving.
- ✅ `apcore-toolkit` 0.9.0 `extract_output_schema` now handles integer OpenAPI
  response-status keys (as emitted by django-ninja) instead of raising
  `TypeError`.

### Changed
- **Bumped SDK floors** to the latest ecosystem release: `apcore>=0.24.0`,
  `apcore-toolkit>=0.8.0`, and `apcore-mcp>=0.16.0` (in the `mcp`/`all` extras).

### Fixed
- **Restored import compatibility with apcore >= 0.18.** `MAX_MODULE_ID_LENGTH`
  and `RESERVED_WORDS` were dropped from `apcore`'s public root (`apcore.__all__`)
  and now live in `apcore.registry.registry`. The top-level import in
  `extensions.py` raised `ImportError` on startup, which broke the entire Django
  app (auto-discovery, executor assembly, every management command). The import
  now falls back to the new location. See *SDK notes* below.
- **Embedded MCP server no longer crashes when `APCORE_OUTPUT_FORMATTER` is set.**
  The non-blocking `MCPServer` class (used for embedded serving) does not accept
  an `output_formatter` argument — only the blocking `apcore_mcp.serve()` path
  does. The setting is now ignored (with a warning) for the embedded server
  instead of raising `TypeError`. Use `manage.py apcore_serve` for formatted
  output. See *SDK notes* below.
- **Embedded MCP server opts out of auth correctly.** `MCPServer` defaults
  `require_auth=True` (apcore-mcp 0.14.0+); the embedded server now sets
  `require_auth=False` when no JWT authenticator is configured, preserving the
  previously-open behavior, and `True` when a JWT authenticator is present.

### Added
- **MCP pipeline / observability serving features** (apcore-mcp 0.13.0–0.16.0),
  exposed via `APCORE_*` settings, `manage.py apcore_serve` flags, and
  `DjangoApcore.serve()`:
  - `APCORE_SERVE_STRATEGY` / `--strategy` — pipeline execution strategy
    (`standard`, `internal`, `testing`, `performance`, `minimal`).
  - `APCORE_SERVE_OUTPUT_FORMAT` / `--output-format` — tabular tool-result
    output (`json`, `csv`, `jsonl`).
  - `APCORE_SERVE_OBSERVABILITY` / `--observability` — auto-wire metrics + usage
    collection and expose `/api/usage` endpoints.
  - `APCORE_SERVE_REDACT_OUTPUT` (default `True`) / `--no-redact-output` —
    control redaction of sensitive fields in tool results.
  - `APCORE_SERVE_TRACE` / `--trace` — per-step pipeline timing traces.
  - `APCORE_EXPLORER_TITLE`, `APCORE_EXPLORER_PROJECT_NAME`,
    `APCORE_EXPLORER_PROJECT_URL` (with matching `--explorer-*` flags) — Tool
    Explorer branding.
- **Embedded MCP server async task bridge** (apcore-mcp 0.14.0+) — the in-process
  task manager is sized from the existing `APCORE_TASK_MAX_CONCURRENT` /
  `APCORE_TASK_MAX_TASKS` settings.

### SDK notes (defects / rough edges reported upstream)
- `apcore`: `MAX_MODULE_ID_LENGTH` / `RESERVED_WORDS` are no longer exported from
  the package root nor re-exported from `apcore.registry`; they are only
  reachable via the deeper `apcore.registry.registry` path. These were
  previously part of the documented public surface — a silent breaking change
  for integrators.
- `apcore-mcp`: the `output_formatter`, `output_format`, `strategy`,
  `observability`, `redact_output`, `trace`, and explorer-branding parameters
  exist on the blocking `serve()` / `APCoreMCP` API but **not** on the
  non-blocking `MCPServer` class used by framework integrations for embedded
  serving. This asymmetry means embedded servers cannot use formatted output or
  pipeline strategies.

## [0.3.1] - 2026-03-22

### Changed
- Rebrand: aipartnerup → aiperceivable

## [0.3.0] - 2026-03-15

### Added

- **`DjangoApcore` unified entry point** — single class for all django-apcore functionality
  - `app.call()`, `app.call_async()`, `app.stream()` with automatic Django request→Context mapping
  - `app.module()` decorator for registering modules
  - `app.scan()` for programmatic endpoint scanning
  - `app.serve()` for starting MCP server
  - `app.to_openai_tools()` for OpenAI export
  - `app.submit_task()`, `app.get_task_status()`, `app.cancel_task()` for async tasks
  - `app.list_modules()`, `app.describe()` for module discovery
  - `DjangoApcore.get_instance()` singleton pattern
  - Lazy property access: `app.registry`, `app.executor`, `app.settings`, etc.
- **apcore-toolkit integration** — replaced local scanner, writer, and OpenAPI implementations
  - `ScannedModule` now supports `documentation`, `examples`, `metadata` fields
  - `annotations` field uses `ModuleAnnotations` instead of `dict[str, bool]`
  - `BaseScanner` gains `extract_docstring()`, `infer_annotations_from_method()`, improved `deduplicate_ids()`
  - OpenAPI utilities (`resolve_ref`, `resolve_schema`, `extract_input_schema`, `extract_output_schema`) now from toolkit
  - Writers (`YAMLWriter`, `PythonWriter`) now from toolkit, returning `WriteResult` with verification support
  - `RegistryWriter` available for direct registry registration
- **Annotation inference** in NinjaScanner and DRFScanner
  - GET → `readonly=True, cacheable=True`
  - DELETE → `destructive=True`
  - PUT → `idempotent=True`
  - Metadata dict includes `http_method` and `url_path`
- **`--output registry`** option for `apcore_scan` — register modules directly without file I/O
- **`--verify`** option for `apcore_scan` — validate generated files (YAML structure, Python syntax)
- **`--ai-enhance`** option for `apcore_scan` — enhance module metadata via local SLM (Ollama/vLLM)
- **`--output-formatter`** option for `apcore_serve` — customize result formatting (e.g., `apcore_toolkit.to_markdown`)
- **`APCORE_OUTPUT_FORMATTER`** setting — configure output formatter globally
- **`APCORE_AI_ENHANCE`** setting — enable AI enhancement by default
- `flatten_pydantic_params` from toolkit used in `DjangoDiscoverer._adapt_view_module()`
- 17 new tests for `DjangoApcore` unified class
- 6 new tests for example project `DjangoApcore` integration
- New tests for `APCORE_OUTPUT_FORMATTER` and `APCORE_AI_ENHANCE` settings

### Changed

- **BREAKING:** `apcore` dependency bumped from `>= 0.6.0` to `>= 0.13.0`
- **BREAKING:** `apcore-mcp` dependency bumped from `>= 0.7.0` to `>= 0.10.0`
- **BREAKING:** `ScannedModule.annotations` type changed from `dict[str, bool] | None` to `ModuleAnnotations | None`
- **BREAKING:** `YAMLWriter.write()` now returns `list[WriteResult]` instead of `list[dict]`
- **BREAKING:** `PythonWriter.write()` now returns `list[WriteResult]` instead of `list[str]`
- **BREAKING:** `BaseScanner.scan()` signature changed from `(include, exclude)` to `(**kwargs)`
- **BREAKING:** `BaseScanner._deduplicate_ids(list[str])` replaced by `deduplicate_ids(list[ScannedModule])`
- Added `apcore-toolkit >= 0.2.0` as a core dependency
- `scanners/base.py` now re-exports from `apcore_toolkit` instead of local implementations
- `output/yaml_writer.py` and `output/python_writer.py` now re-export from `apcore_toolkit`
- `extensions.py` uses `flatten_pydantic_params` for Pydantic model handling
- Example project `task_stats.py` updated to use `@app.module()` via `DjangoApcore`
- Version bumped to 0.3.0

### Testing

- 465 tests (up from 448 in 0.2.0) + 21 example project tests
- All tests passing with lint clean

## [0.2.0] - 2026-02-28

### Added

- **JWT authentication** for the MCP server (requires `apcore-mcp >= 0.7.0`)
  - 4 new Django settings: `APCORE_JWT_SECRET`, `APCORE_JWT_ALGORITHM`, `APCORE_JWT_AUDIENCE`, `APCORE_JWT_ISSUER`
  - 4 new CLI flags for `apcore_serve`: `--jwt-secret`, `--jwt-algorithm`, `--jwt-audience`, `--jwt-issuer`
  - CLI flags override Django settings; JWT is opt-in (disabled when `APCORE_JWT_SECRET` is not set)
  - Embedded MCP server (`APCORE_EMBEDDED_SERVER`) also supports JWT when configured
  - JWT `sub` claim is mapped to an apcore `Identity`
- `authenticator` parameter on the `serve()` wrapper function
- Example project updated with JWT configuration (settings, `.env.example`, `docker-compose.yml`, README)

### Changed

- Bumped `apcore-mcp` dependency floor from `>= 0.6.0` to `>= 0.7.0` (for `apcore_mcp.auth.JWTAuthenticator`)
- README settings table and CLI flags table updated with JWT options

### Testing

- 434 tests (up from 393 in 0.1.0)
- New test classes: `TestJWTSettings`, `TestApcoreServeJWT`, and JWT-related embedded server tests

## [0.1.1] - 2026-02-24

### Fixed

- Removed outdated version check from `test_init.py`
- Removed ruff format check from CI workflow

### Changed

- Updated project URLs in `pyproject.toml`

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

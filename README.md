# django-apcore

Django integration for the [apcore](https://github.com/aiperceivable/apcore) protocol — scan your existing Django REST APIs and serve them as MCP tools for AI agents.

## Overview

**django-apcore** bridges your existing Django REST Framework and django-ninja endpoints to the [apcore](https://github.com/aiperceivable/apcore) protocol, enabling them to be served as [MCP](https://modelcontextprotocol.io/) (Model Context Protocol) tools that AI agents can discover and invoke.

The core philosophy is **scan, don't rewrite**: instead of manually defining MCP tools alongside your API endpoints, django-apcore auto-scans your existing OpenAPI schemas (via drf-spectacular or django-ninja) and generates apcore module definitions. These modules are then served to AI agents through apcore-mcp.

## Key Features

- **`DjangoApcore` unified entry point** — single class for all django-apcore functionality
- **Auto-scan DRF endpoints** via drf-spectacular OpenAPI generation
- **Auto-scan django-ninja endpoints** via built-in OpenAPI schema extraction
- **Auto-resolve `$ref`** — Pydantic model schemas resolved from OpenAPI `$ref` references
- **Annotation inference** — GET→readonly/cacheable, DELETE→destructive, PUT→idempotent
- **Semantic module IDs** — action verbs from function names (`list`, `get`, `create`) instead of raw HTTP methods
- **Three output formats** — YAML bindings, Python `@module` wrappers, or direct registry registration
- **Output verification** — validate generated files for syntax and structure
- **AI enhancement** — auto-enhance module metadata via local SLMs (Ollama/vLLM)
- **Serve as MCP tools** via apcore-mcp (stdio / streamable-http / SSE transports)
- **Output formatting** — Markdown or custom formatters for LLM-friendly results
- **Pluggable middleware pipeline** — logging, tracing, metrics, and custom middleware
- **YAML-based access control (ACL)** for fine-grained module permissions
- **Django context factory** — maps `request.user` to apcore `Identity` automatically
- **Embedded MCP server mode** — start MCP server alongside Django on startup
- **Include/exclude endpoint filtering** with regex patterns
- **Export to OpenAI tool format** for non-MCP integrations
- **Tool Explorer** — browser-based UI for browsing schemas and testing tools interactively
- **JWT authentication** — Bearer token auth on the MCP server

## How It Works

```
Django Endpoints (DRF / django-ninja)
        │
        ▼
   ┌─────────┐     ┌───────────────┐
   │ Scanner  │────▶│ ScannedModule │  ← annotations auto-inferred
   └─────────┘     └───────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     YAML bindings   Python @module   Registry
              │            │            │  (direct)
              └────────────┴────────────┘
                           ▼
                    ┌──────────┐
                    │ Registry │
                    └────┬─────┘
                         ▼
                    ┌──────────┐    ┌─────────────┐
                    │ Executor │───▶│ Middlewares  │
                    └────┬─────┘    │ ACL / Tracing│
                         │         └─────────────┘
                         ▼
                    ┌───────────┐
                    │ apcore-mcp│
                    └────┬──────┘
                         ▼
                   MCP Transport
              (stdio / HTTP / SSE)
                         │
                         ▼
                    AI Agent
```

## Quick Start

### 1. Install

```bash
pip install django-apcore[all]
```

### 2. Add to Django settings

```python
INSTALLED_APPS = [
    # ...
    "django_apcore",
]

APCORE_MODULE_DIR = "apcore_modules/"
```

### 3. Scan your endpoints

```bash
# Generate YAML bindings from django-ninja routes
python manage.py apcore_scan --source ninja --output yaml

# Or register directly into the registry (no files)
python manage.py apcore_scan --source ninja --output registry

# Scan DRF endpoints
python manage.py apcore_scan --source drf --output yaml

# Preview without writing
python manage.py apcore_scan --source ninja --dry-run

# Filter with regex
python manage.py apcore_scan --source drf --include "users.*" --exclude "admin.*"
```

### 4. Serve as MCP tools

```bash
# Start MCP server (stdio, default)
python manage.py apcore_serve

# HTTP transport with explorer UI
python manage.py apcore_serve --transport streamable-http --port 9090 --explorer
```

## DjangoApcore — Unified Entry Point

`DjangoApcore` is the recommended way to use django-apcore. It provides a single class for all functionality, following the same pattern as `apcore.APCore` and `apcore_mcp.APCoreMCP`.

```python
from django_apcore import DjangoApcore

app = DjangoApcore()
```

### Register modules

```python
from apcore import ModuleAnnotations

@app.module(
    id="analytics.task_stats",
    tags=["analytics"],
    annotations=ModuleAnnotations(readonly=True, cacheable=True),
)
def task_stats() -> dict:
    """Return summary statistics about all tasks."""
    return {"total": 42, "done": 10, "pending": 32}
```

### Call modules from Django views

```python
from django.http import JsonResponse
from django_apcore import DjangoApcore

app = DjangoApcore()

# Sync view — request auto-maps to apcore Identity
def my_view(request):
    result = app.call("analytics.task_stats", request=request)
    return JsonResponse(result)

# Async view
async def my_async_view(request):
    result = await app.call_async("analytics.task_stats", request=request)
    return JsonResponse(result)

# Streaming
async def my_stream_view(request):
    async for chunk in app.stream("ai.chat", {"prompt": "hello"}, request=request):
        yield chunk

# With cancellation timeout
result = app.cancellable_call("slow.module", timeout=30, request=request)
```

### Scan, list, and describe

```python
# Scan endpoints programmatically
modules = app.scan(source="ninja", include="users")

# List registered modules
ids = app.list_modules(tags=["analytics"])

# Get module description (for LLM use)
desc = app.describe("analytics.task_stats")
```

### Task management

```python
# Submit async task
task_id = await app.submit_task("heavy.report", {"year": 2026})

# Check status
status = app.get_task_status(task_id)

# Cancel
await app.cancel_task(task_id)
```

### MCP serving and export

```python
# Start MCP server (blocking)
app.serve(transport="streamable-http", port=9090, explorer=True)

# Export as OpenAI tools
tools = app.to_openai_tools(tags=["public"], strict=True)
```

### Singleton access

```python
# Process-wide singleton (for use across modules)
app = DjangoApcore.get_instance()
```

### Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `app.registry` | `Registry` | apcore Registry singleton |
| `app.executor` | `Executor` | apcore Executor with extensions applied |
| `app.extension_manager` | `ExtensionManager` | Extension point manager |
| `app.context_factory` | `ContextFactory` | Django request → apcore Context |
| `app.metrics_collector` | `MetricsCollector \| None` | Metrics (if enabled) |
| `app.task_manager` | `AsyncTaskManager` | Async task manager |
| `app.settings` | `ApcoreSettings` | Validated Django settings |

## Installation

Install with pip, choosing the extras you need:

```bash
# All optional dependencies
pip install django-apcore[all]

# Only django-ninja scanner
pip install django-apcore[ninja]

# Only DRF scanner (via drf-spectacular)
pip install django-apcore[drf]

# Only MCP server support
pip install django-apcore[mcp]
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `django` | `>= 4.2` | Core framework |
| `apcore` | `>= 0.13.0` | Protocol SDK |
| `apcore-toolkit` | `>= 0.2.0` | Scanner, writer, and formatting utilities |
| `pyyaml` | `>= 6.0` | YAML binding files |

### Optional Dependencies

| Extra | Package | Version | Purpose |
|-------|---------|---------|---------|
| `ninja` | `django-ninja` | `>= 1.0` | django-ninja endpoint scanning |
| `drf` | `drf-spectacular` | `>= 0.27` | DRF endpoint scanning via OpenAPI |
| `mcp` | `apcore-mcp` | `>= 0.10.0` | MCP server, transport layer, JWT auth, Tool Explorer |

## Configuration

All settings are prefixed with `APCORE_` and read from Django's `settings.py`.

### Core Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `APCORE_MODULE_DIR` | `str` | `"apcore_modules/"` | Directory for YAML binding files and `@module` Python files |
| `APCORE_AUTO_DISCOVER` | `bool` | `True` | Auto-discover bindings and `@module` functions on Django startup |
| `APCORE_BINDING_PATTERN` | `str` | `"*.binding.yaml"` | Glob pattern for discovering YAML binding files |
| `APCORE_CONTEXT_FACTORY` | `str \| None` | `None` | Dotted path to custom ContextFactory class |
| `APCORE_EXECUTOR_CONFIG` | `dict \| None` | `None` | Additional executor configuration dict |
| `APCORE_VALIDATE_INPUTS` | `bool` | `False` | Enable input validation at the executor layer |

### MCP Server Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `APCORE_SERVE_TRANSPORT` | `str` | `"stdio"` | MCP transport: `"stdio"`, `"streamable-http"`, or `"sse"` |
| `APCORE_SERVE_HOST` | `str` | `"127.0.0.1"` | Host for HTTP-based transports |
| `APCORE_SERVE_PORT` | `int` | `9090` | Port for HTTP-based transports (1–65535) |
| `APCORE_SERVER_NAME` | `str` | `"apcore-mcp"` | MCP server name (1–100 characters) |
| `APCORE_SERVER_VERSION` | `str \| None` | `None` | Server version string |
| `APCORE_OUTPUT_FORMATTER` | `str \| None` | `None` | Dotted path to output formatter (e.g., `"apcore_toolkit.to_markdown"`) |

### Extension Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `APCORE_MIDDLEWARES` | `list[str]` | `[]` | Dotted paths to middleware classes |
| `APCORE_ACL_PATH` | `str \| None` | `None` | Path to YAML ACL file for access control |
| `APCORE_MODULE_VALIDATORS` | `list[str]` | `[]` | Dotted paths to extra module validator classes |

### Explorer Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `APCORE_EXPLORER_ENABLED` | `bool` | `False` | Enable the browser-based Tool Explorer UI |
| `APCORE_EXPLORER_PREFIX` | `str` | `"/explorer"` | URL prefix for the explorer UI |
| `APCORE_EXPLORER_ALLOW_EXECUTE` | `bool` | `False` | Allow tool execution from the explorer UI |

### JWT Authentication Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `APCORE_JWT_SECRET` | `str \| None` | `None` | JWT secret/key. Enables JWT auth when set |
| `APCORE_JWT_ALGORITHM` | `str` | `"HS256"` | JWT algorithm (e.g., `HS256`, `RS256`) |
| `APCORE_JWT_AUDIENCE` | `str \| None` | `None` | Expected JWT `aud` claim |
| `APCORE_JWT_ISSUER` | `str \| None` | `None` | Expected JWT `iss` claim |

### AI Enhancement Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `APCORE_AI_ENHANCE` | `bool` | `False` | Enable AI enhancement in `apcore_scan` |

AI enhancement also requires the `APCORE_AI_ENABLED=true` environment variable and a running SLM (Ollama/vLLM). See [apcore-toolkit](https://github.com/aiperceivable/apcore-toolkit-python) for configuration.

### Observability Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `APCORE_OBSERVABILITY_LOGGING` | `bool \| dict \| None` | `None` | Enable observability logging middleware |
| `APCORE_TRACING` | `bool \| dict \| None` | `None` | Enable tracing (stdout, in_memory, otlp) |
| `APCORE_METRICS` | `bool \| dict \| None` | `None` | Enable metrics collection |

<details>
<summary>Observability dict options</summary>

```python
# Logging
APCORE_OBSERVABILITY_LOGGING = {
    "log_inputs": True,
    "log_outputs": True,
    "level": "info",          # trace, debug, info, warn, error, fatal
    "format": "json",
    "redact_sensitive": True,
}

# Tracing
APCORE_TRACING = {
    "exporter": "otlp",              # stdout, in_memory, otlp
    "sampling_rate": 0.1,            # 0.0 to 1.0
    "sampling_strategy": "full",     # full, proportional, error_first, off
    "otlp_endpoint": "http://localhost:4318",
    "otlp_service_name": "my-django-app",
}

# Metrics
APCORE_METRICS = {
    "buckets": [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
}
```

</details>

### Embedded Server Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `APCORE_EMBEDDED_SERVER` | `bool \| dict \| None` | `None` | Start an embedded MCP server on Django startup |

```python
APCORE_EMBEDDED_SERVER = {
    "transport": "streamable-http",
    "host": "127.0.0.1",
    "port": 9090,
    "name": "embedded-mcp",
}
```

### Task & Cancellation Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `APCORE_TASK_MAX_CONCURRENT` | `int` | `10` | Max concurrent async tasks |
| `APCORE_TASK_MAX_TASKS` | `int` | `1000` | Max total tasks in queue |
| `APCORE_TASK_CLEANUP_AGE` | `int` | `3600` | Seconds before completed tasks are cleaned up |
| `APCORE_CANCEL_DEFAULT_TIMEOUT` | `int \| None` | `None` | Default cancellation timeout (seconds) |

## Management Commands

### `apcore_scan`

Scan Django API endpoints and generate apcore module definitions.

```bash
python manage.py apcore_scan --source <ninja|drf> [options]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--source` | `-s` | **Required.** Scanner source: `ninja` or `drf` |
| `--output` | `-o` | Output format: `yaml` (default), `python`, or `registry` |
| `--dir` | `-d` | Output directory (default: `APCORE_MODULE_DIR`) |
| `--dry-run` | | Preview output without writing files |
| `--verify` | | Verify written output files (YAML validity, Python syntax) |
| `--include` | | Regex pattern to include endpoints |
| `--exclude` | | Regex pattern to exclude endpoints |
| `--ai-enhance` | | Enhance module metadata via local SLM |

### `apcore_serve`

Start an MCP server with registered apcore modules.

```bash
python manage.py apcore_serve [options]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--transport` | `-t` | `stdio`, `streamable-http`, or `sse` |
| `--host` | | Host for HTTP transports |
| `--port` | `-p` | Port for HTTP transports |
| `--name` | | MCP server name |
| `--server-version` | | Server version string |
| `--explorer` | | Enable the browser-based Tool Explorer UI (HTTP only) |
| `--explorer-prefix` | | URL prefix for the explorer UI (default: `/explorer`) |
| `--allow-execute` | | Allow tool execution from the explorer UI |
| `--validate-inputs` | | Enable input validation |
| `--metrics` | | Enable Prometheus `/metrics` endpoint |
| `--log-level` | | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `--tags` | | Filter modules by tags (comma-separated) |
| `--prefix` | | Filter modules by ID prefix |
| `--output-formatter` | | Dotted path to output formatter (e.g., `apcore_toolkit.to_markdown`) |
| `--jwt-secret` | | JWT secret/key for authentication |
| `--jwt-algorithm` | | JWT algorithm (default: `HS256`) |
| `--jwt-audience` | | Expected JWT `aud` claim |
| `--jwt-issuer` | | Expected JWT `iss` claim |

### `apcore_export`

Export registered modules to OpenAI tool format.

```bash
python manage.py apcore_export [options]
```

| Option | Description |
|--------|-------------|
| `--format` | Export format: `openai-tools` (default) |
| `--strict` | Enable strict mode for OpenAI Structured Outputs |
| `--embed-annotations` | Embed module annotations in output |
| `--tags` | Filter by tags (space-separated) |
| `--prefix` | Prefix for tool names |

### `apcore_tasks`

Manage async tasks.

```bash
python manage.py apcore_tasks <list|cancel|cleanup> [options]
```

## Legacy API (Shortcuts)

For projects not using `DjangoApcore`, the function-based shortcuts are still available:

```python
from django_apcore.shortcuts import (
    executor_call,          # sync call
    executor_call_async,    # async call
    executor_stream,        # streaming
    cancellable_call,       # call with CancelToken
    cancellable_call_async, # async cancellable
    submit_task,            # submit async task
    get_task_status,        # query task status
    cancel_task,            # cancel task
    report_progress,        # MCP progress
    elicit,                 # MCP user input
)

# Example
def my_view(request):
    result = executor_call("users.list", {"page": 1}, request=request)
    return JsonResponse(result)
```

## Comparison with Other MCP Solutions

| Feature | django-apcore | django-mcp-server | django-mcp | django-ninja-mcp | FastMCP | fastapi-mcp |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Approach** | Scan existing endpoints | Define new tools | Define new tools | Scan ninja endpoints | Define new tools | Scan FastAPI endpoints |
| **DRF support** | Yes (via drf-spectacular) | Yes (opt-in decorators) | No | No | No (not Django) | No (FastAPI only) |
| **django-ninja support** | Yes | No | No | Yes | No (not Django) | No (FastAPI only) |
| **Unified client class** | `DjangoApcore` | No | No | No | No | No |
| **Schema source** | Auto from OpenAPI | Model/serializer introspection | Manual | Auto from OpenAPI | Manual | Auto from OpenAPI |
| **Transport: stdio** | Yes | Yes | No | No | Yes | No |
| **Transport: streamable-http** | Yes | Yes | No | No | Yes | Yes |
| **Transport: SSE** | Yes | No | Yes | Yes | Yes | Yes |
| **Annotation inference** | Yes | No | No | No | No | No |
| **Output verification** | Yes | No | No | No | No | No |
| **AI enhancement** | Yes | No | No | No | No | No |
| **Tracing (OpenTelemetry)** | Yes | No | No | No | Yes | No |
| **Metrics collection** | Yes | No | No | No | No | No |
| **Middleware pipeline** | Yes | No | No | No | Yes | No |
| **YAML-based ACL** | Yes | No | No | No | No | No |
| **Identity mapping** | Yes (Django User) | DRF auth classes | No | No | Per-component auth | FastAPI Depends() |
| **Export to OpenAI tools** | Yes | No | No | No | No | No |
| **JWT authentication** | Yes | No | No | No | No | No |

## Demo Project

The `example/` directory contains a Task Manager API demo showcasing all major features.

```bash
cd example
docker compose up --build
```

| Service | URL | Description |
|---------|-----|-------------|
| `web` | http://localhost:8000 | Django API server (django-ninja) |
| `mcp` | http://localhost:9090 | MCP server with Tool Explorer |

See [`example/README.md`](example/README.md) for full setup instructions and `DjangoApcore` usage examples.

## Requirements

- Python 3.11+
- Django 4.2+ (including 5.0, 5.1, 6.0)

## License

MIT

# django-apcore

Django integration for the [apcore](https://github.com/aipartnerup/apcore) protocol — scan your existing Django REST APIs and serve them as MCP tools for AI agents.

## Overview

**django-apcore** bridges your existing Django REST Framework and django-ninja endpoints to the [apcore](https://github.com/aipartnerup/apcore) protocol, enabling them to be served as [MCP](https://modelcontextprotocol.io/) (Model Context Protocol) tools that AI agents can discover and invoke.

The core philosophy is **scan, don't rewrite**: instead of manually defining MCP tools alongside your API endpoints, django-apcore auto-scans your existing OpenAPI schemas (via drf-spectacular or django-ninja) and generates apcore module definitions. These modules are then served to AI agents through apcore-mcp.

## Key Features

- **Auto-scan DRF endpoints** via drf-spectacular OpenAPI generation
- **Auto-scan django-ninja endpoints** via built-in OpenAPI schema extraction
- **Auto-resolve `$ref`** — Pydantic model schemas resolved from OpenAPI `$ref` references
- **Semantic module IDs** — action verbs from function names (`list`, `get`, `create`) instead of raw HTTP methods
- **Generate YAML binding files** or **Python `@module` wrappers** from scanned endpoints
- **Serve as MCP tools** via apcore-mcp (stdio / streamable-http / SSE transports)
- **Pluggable middleware pipeline** — logging, tracing, metrics, and custom middleware
- **YAML-based access control (ACL)** for fine-grained module permissions
- **Django context factory** — maps `request.user` to apcore `Identity` automatically
- **Embedded MCP server mode** — start MCP server alongside Django on startup
- **Include/exclude endpoint filtering** with regex patterns
- **Export to OpenAI tool format** for non-MCP integrations
- **Tool Explorer** — browser-based UI for browsing schemas and testing tools interactively (via apcore-mcp)
- **Convenience shortcuts** — `executor_call`, `executor_call_async`, `executor_stream`, `report_progress`, `elicit`

## How It Works

```
Django Endpoints (DRF / django-ninja)
        │
        ▼
   ┌─────────┐     ┌───────────────┐
   │ Scanner  │────▶│ ScannedModule │
   └─────────┘     └───────┬───────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
     YAML .binding files       Python @module files
              │                         │
              └────────────┬────────────┘
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

1. **Scan** — `apcore_scan` introspects your API framework and extracts endpoint metadata (schemas, descriptions, tags) into `ScannedModule` objects.
2. **Generate** — Output writers produce YAML binding files or Python `@module` wrapper files.
3. **Register** — On Django startup, `ApcoreAppConfig.ready()` auto-discovers binding files and `@module` functions, registering them with the apcore `Registry`.
4. **Serve** — `apcore_serve` starts an MCP server (via apcore-mcp) that exposes all registered modules as MCP tools.

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

# Optional: configure module directory and transport
APCORE_MODULE_DIR = "apcore_modules/"
APCORE_SERVE_TRANSPORT = "stdio"
```

### 3. Scan your endpoints

```bash
# Scan django-ninja endpoints, output as YAML bindings
python manage.py apcore_scan --source ninja --output yaml

# Scan DRF endpoints, output as Python @module wrappers
python manage.py apcore_scan --source drf --output python

# Preview without writing files
python manage.py apcore_scan --source ninja --dry-run

# Filter endpoints with regex
python manage.py apcore_scan --source drf --include "users.*" --exclude "admin.*"
```

### 4. Serve as MCP tools

```bash
# Start MCP server (stdio transport, default)
python manage.py apcore_serve

# Start with HTTP transport
python manage.py apcore_serve --transport streamable-http --host 0.0.0.0 --port 9090
```

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
| `apcore` | `>= 0.6.0` | Protocol SDK |
| `pydantic` | `>= 2.0` | Schema validation |
| `pyyaml` | `>= 6.0` | YAML binding files |

### Optional Dependencies

| Extra | Package | Version | Purpose |
|-------|---------|---------|---------|
| `ninja` | `django-ninja` | `>= 1.0` | django-ninja endpoint scanning |
| `drf` | `drf-spectacular` | `>= 0.27` | DRF endpoint scanning via OpenAPI |
| `mcp` | `apcore-mcp` | `>= 0.6.0` | MCP server and transport layer |

## Configuration

All settings are prefixed with `APCORE_` and read from Django's `settings.py`.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `APCORE_MODULE_DIR` | `str` | `"apcore_modules/"` | Directory for YAML binding files and `@module` Python files |
| `APCORE_AUTO_DISCOVER` | `bool` | `True` | Auto-discover bindings and `@module` functions on Django startup |
| `APCORE_SERVE_TRANSPORT` | `str` | `"stdio"` | MCP transport: `"stdio"`, `"streamable-http"`, or `"sse"` |
| `APCORE_SERVE_HOST` | `str` | `"127.0.0.1"` | Host for HTTP-based transports |
| `APCORE_SERVE_PORT` | `int` | `8000` | Port for HTTP-based transports (1–65535) |
| `APCORE_SERVER_NAME` | `str` | `"apcore-mcp"` | MCP server name (1–100 characters) |
| `APCORE_SERVER_VERSION` | `str \| None` | `None` | Server version string |
| `APCORE_BINDING_PATTERN` | `str` | `"*.binding.yaml"` | Glob pattern for discovering YAML binding files |
| `APCORE_MIDDLEWARES` | `list[str]` | `[]` | Dotted paths to middleware classes |
| `APCORE_ACL_PATH` | `str \| None` | `None` | Path to YAML ACL file for access control |
| `APCORE_CONTEXT_FACTORY` | `str \| None` | `None` | Dotted path to custom ContextFactory class |
| `APCORE_EXECUTOR_CONFIG` | `dict \| None` | `None` | Additional executor configuration dict |
| `APCORE_VALIDATE_INPUTS` | `bool` | `False` | Enable input validation at the MCP layer |
| `APCORE_OBSERVABILITY_LOGGING` | `bool \| dict \| None` | `None` | Enable observability logging middleware |
| `APCORE_TRACING` | `bool \| dict \| None` | `None` | Enable tracing middleware (stdout, in_memory, otlp) |
| `APCORE_METRICS` | `bool \| dict \| None` | `None` | Enable metrics collection middleware |
| `APCORE_EMBEDDED_SERVER` | `bool \| dict \| None` | `None` | Start an embedded MCP server on Django startup |
| `APCORE_EXPLORER_ENABLED` | `bool` | `False` | Enable the browser-based Tool Explorer UI on the MCP server |
| `APCORE_EXPLORER_PREFIX` | `str` | `"/explorer"` | URL prefix for the explorer UI |
| `APCORE_EXPLORER_ALLOW_EXECUTE` | `bool` | `False` | Allow tool execution from the explorer UI |

### Observability Logging Options

When `APCORE_OBSERVABILITY_LOGGING` is a dict:

```python
APCORE_OBSERVABILITY_LOGGING = {
    "log_inputs": True,       # Log module inputs
    "log_outputs": True,      # Log module outputs
    "level": "info",          # trace, debug, info, warn, error, fatal
    "format": "json",         # Log format
    "redact_sensitive": True,  # Redact sensitive data
}
```

### Tracing Options

When `APCORE_TRACING` is a dict:

```python
APCORE_TRACING = {
    "exporter": "otlp",              # stdout, in_memory, otlp, or dotted path
    "sampling_rate": 0.1,            # 0.0 to 1.0
    "sampling_strategy": "full",     # full, proportional, error_first, off
    "otlp_endpoint": "http://localhost:4318",
    "otlp_service_name": "my-django-app",
}
```

### Metrics Options

When `APCORE_METRICS` is a dict:

```python
APCORE_METRICS = {
    "buckets": [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
}
```

### Embedded Server Options

When `APCORE_EMBEDDED_SERVER` is a dict:

```python
APCORE_EMBEDDED_SERVER = {
    "transport": "streamable-http",
    "host": "127.0.0.1",
    "port": 9090,
    "name": "embedded-mcp",
    "version": "1.0.0",
}
```

### Tool Explorer

The Tool Explorer is a browser-based UI provided by [apcore-mcp](https://github.com/aipartnerup/apcore-mcp-python) for browsing tool schemas and testing tool execution interactively. It runs on the MCP server port (not the Django port).

```python
# settings.py
APCORE_EXPLORER_ENABLED = True          # enable explorer UI
APCORE_EXPLORER_ALLOW_EXECUTE = True    # allow Try-it execution
# APCORE_EXPLORER_PREFIX = "/explorer"  # default prefix
```

Or via CLI flags:

```bash
python manage.py apcore_serve --transport streamable-http --explorer --allow-execute
# Open http://127.0.0.1:8000/explorer/ in a browser
```

**Endpoints** (served by apcore-mcp on the MCP port):

| Endpoint | Description |
|----------|-------------|
| `GET /explorer/` | Interactive HTML page (self-contained, no external dependencies) |
| `GET /explorer/tools` | JSON array of all tools with name, description, annotations |
| `GET /explorer/tools/<name>` | Full tool detail with inputSchema |
| `POST /explorer/tools/<name>/call` | Execute a tool (requires `allow_execute=True`) |

- **HTTP transports only** (`streamable-http`, `sse`). Silently ignored for `stdio`.
- **Execution disabled by default** — set `APCORE_EXPLORER_ALLOW_EXECUTE = True` or `--allow-execute` to enable.
- **No auth** — do NOT enable in production without a reverse proxy.

## Management Commands

### `apcore_scan`

Scan Django API endpoints and generate apcore module definitions.

```bash
python manage.py apcore_scan --source <ninja|drf> [options]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--source` | `-s` | **Required.** Scanner source: `ninja` or `drf` |
| `--output` | `-o` | Output format: `yaml` (default) or `python` |
| `--dir` | `-d` | Output directory (default: `APCORE_MODULE_DIR`) |
| `--dry-run` | | Preview output without writing files |
| `--include` | | Regex pattern to include endpoints |
| `--exclude` | | Regex pattern to exclude endpoints |

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
| `--validate-inputs` | | Enable input validation on the MCP server |
| `--metrics` | | Enable Prometheus `/metrics` endpoint |
| `--log-level` | | MCP server log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `--tags` | | Filter modules by tags (comma-separated) |
| `--prefix` | | Filter modules by ID prefix |

### `apcore_export`

Export registered modules to external tool formats.

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

## Shortcuts

Convenience functions for calling apcore modules from Django views without manually wiring together the registry, executor, and context factory.

```python
from django_apcore.shortcuts import (
    executor_call,
    executor_call_async,
    executor_stream,
    report_progress,
    elicit,
)
```

### `executor_call(module_id, inputs, *, request, context)`

Execute an apcore module synchronously.

```python
# In a Django view
def my_view(request):
    result = executor_call("users.list", {"page": 1}, request=request)
    return JsonResponse(result)
```

### `executor_call_async(module_id, inputs, *, request, context)`

Execute an apcore module asynchronously.

```python
async def my_async_view(request):
    result = await executor_call_async("users.create", {"name": "Alice"}, request=request)
    return JsonResponse(result)
```

### `executor_stream(module_id, inputs, *, request, context)`

Stream an apcore module's output asynchronously.

```python
async def my_streaming_view(request):
    async for chunk in executor_stream("reports.generate", {"id": 42}, request=request):
        yield chunk
```

### `report_progress(context, progress, total, message)`

Report execution progress to the MCP client. No-ops when apcore-mcp is not installed.

### `elicit(context, message, requested_schema)`

Ask the MCP client for user input via elicitation. Returns `None` when apcore-mcp is not installed.

## Comparison with Other MCP Solutions

| Feature | django-apcore | django-mcp-server | django-mcp | django-ninja-mcp | FastMCP | fastapi-mcp |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Approach** | Scan existing endpoints | Define new tools | Define new tools | Scan ninja endpoints | Define new tools | Scan FastAPI endpoints |
| **DRF support** | Yes (via drf-spectacular) | Yes (opt-in decorators) | No | No | No (not Django) | No (FastAPI only) |
| **django-ninja support** | Yes | No | No | Yes | No (not Django) | No (FastAPI only) |
| **Schema source** | Auto from OpenAPI | Model/serializer introspection | Manual | Auto from OpenAPI | Manual | Auto from OpenAPI |
| **Transport: stdio** | Yes | Yes | No | No | Yes | No |
| **Transport: streamable-http** | Yes | Yes | No | No | Yes | Yes |
| **Transport: SSE** | Yes | No | Yes | Yes | Yes | Yes |
| **Tracing (OpenTelemetry)** | Yes | No | No | No | Yes | No |
| **Metrics collection** | Yes | No | No | No | No | No |
| **Observability logging** | Yes | No | No | No | Yes | No |
| **Middleware pipeline** | Yes | No | No | No | Yes | No |
| **YAML-based ACL** | Yes | No | No | No | No | No |
| **Identity mapping** | Yes (Django User) | DRF auth classes | No | No | Per-component auth | FastAPI Depends() |
| **Embedded server mode** | Yes | No | No | No | No | Yes |
| **Output: YAML bindings** | Yes | N/A | N/A | No | N/A | N/A |
| **Output: Python @module** | Yes | N/A | N/A | No | N/A | N/A |
| **Export to OpenAI tools** | Yes | No | No | No | No | No |
| **Django framework** | Yes | Yes | Yes | Yes | No | No |

### Key Differentiators

- **Scan, don't rewrite** — django-apcore scans your existing API endpoints and generates module definitions automatically. No need to duplicate endpoint logic as MCP tool definitions.
- **Dual framework support** — First-class support for both DRF (via drf-spectacular) and django-ninja in a single package.
- **Full observability stack** — Built-in logging, OpenTelemetry tracing (stdout / in-memory / OTLP exporters), and metrics collection via pluggable middleware.
- **YAML-based ACL** — Declarative access control without code changes.
- **Django-native identity** — Automatically maps `request.user` (including groups, staff/superuser status) to apcore `Identity` for ACL evaluation.

## Demo Project

The `example/` directory contains a Task Manager API demo showcasing django-apcore's core features: django-ninja route scanning, `@module` decorator, MCP server with Tool Explorer, and observability.

### Run with Docker

```bash
cd example
docker compose up --build
```

This starts two services:

| Service | URL | Description |
|---------|-----|-------------|
| `web` | http://localhost:8000 | Django API server (django-ninja) |
| `mcp` | http://localhost:9090 | MCP server (`apcore_serve`, streamable-http) |

### Registered Modules

| Module ID | Target | Description |
|-----------|--------|-------------|
| `task_stats.v1` | `task_stats()` | Return summary statistics about all tasks |
| `api.tasks.list` | `list_tasks()` | List all tasks |
| `api.tasks.get` | `get_task(task_id)` | Get a task by its ID |
| `api.tasks.create` | `create_task(body)` | Create a new task |
| `api.tasks.update` | `update_task(task_id, body)` | Update an existing task |
| `api.tasks.delete` | `delete_task(task_id)` | Delete a task permanently |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List all tasks |
| POST | `/api/tasks` | Create a new task |
| GET | `/api/tasks/{task_id}` | Get a task by ID |
| PUT | `/api/tasks/{task_id}` | Update a task |
| DELETE | `/api/tasks/{task_id}` | Delete a task |

### Try It

```bash
# List tasks
curl http://localhost:8000/api/tasks

# Create a task
curl -X POST http://localhost:8000/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Buy milk", "description": "From the store"}'

# Get a task by ID
curl http://localhost:8000/api/tasks/1

# Update a task
curl -X PUT http://localhost:8000/api/tasks/1 \
  -H 'Content-Type: application/json' \
  -d '{"done": true}'

# Delete a task
curl -X DELETE http://localhost:8000/api/tasks/2
```

### Connect an AI Agent

The MCP server on port 9090 uses the `streamable-http` transport. Point any MCP-compatible AI agent to `http://localhost:9090` to discover and invoke the registered modules as tools.

### Demo Project Structure

```
example/
├── Dockerfile              # Python 3.11 image with django-apcore
├── docker-compose.yml      # web + mcp services
├── entrypoint.sh           # scan → serve pipeline
├── manage.py
├── conftest.py             # pytest-django configuration
├── demo/
│   ├── settings.py         # Django settings with apcore config
│   ├── urls.py             # API route (django-ninja)
│   ├── api.py              # Task Manager CRUD with Pydantic schemas
│   └── apcore_modules/
│       ├── __init__.py     # Re-exports for auto-discovery
│       ├── task_stats.py   # @module "task_stats.v1"
│       └── *.binding.yaml  # Auto-generated YAML bindings for scanned routes
└── tests/
    └── test_demo.py        # Unit + integration tests
```

## Requirements

- Python 3.11+
- Django 4.2+ (including 5.0 and 5.1)

## License

MIT

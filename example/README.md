# django-apcore Demo

Task Manager API demonstrating django-ninja routes → NinjaScanner → Registry → MCP Server pipeline with the `DjangoApcore` unified entry point.

## What's Inside

| File | Purpose |
|---|---|
| `demo/api.py` | Task Manager CRUD API with Pydantic schemas (django-ninja) |
| `demo/apcore_modules/task_stats.py` | `@app.module()` example using `DjangoApcore` |
| `Dockerfile` | Installs django-apcore[all] from local source |
| `docker-compose.yml` | One-click Docker launch |
| `entrypoint.sh` | Scans routes then starts the MCP server |

## Quick Start with DjangoApcore

```python
from django_apcore import DjangoApcore

app = DjangoApcore()

# Register a module
@app.module(id="task_stats.v1", tags=["analytics"])
def task_stats() -> dict:
    return {"total": 10, "done": 3, "pending": 7}

# Call from a Django view
def my_view(request):
    result = app.call("task_stats.v1", request=request)
    return JsonResponse(result)

# Async call
async def my_async_view(request):
    result = await app.call_async("task_stats.v1", request=request)
    return JsonResponse(result)

# Scan endpoints programmatically
modules = app.scan(source="ninja")

# List registered modules
module_ids = app.list_modules(tags=["analytics"])

# Export as OpenAI tools
tools = app.to_openai_tools()

# Start MCP server
app.serve(transport="streamable-http", port=9090, explorer=True)
```

## Local Development

### Prerequisites

From the project root, install django-apcore in editable mode with all extras:

```bash
pip install -e ".[all]"
```

### 1. Scan routes

```bash
cd example
export DJANGO_SETTINGS_MODULE=demo.settings

# Generate YAML bindings (with verification)
python manage.py apcore_scan --source ninja --output yaml --dir ./demo/apcore_modules --verify

# Or register directly into the registry (no files written)
python manage.py apcore_scan --source ninja --output registry
```

### 2. Start the Django dev server

```bash
python manage.py runserver
```

### 3. Start the MCP server (separate terminal)

```bash
python manage.py apcore_serve \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 9090 \
  --validate-inputs \
  --log-level DEBUG \
  --explorer
```

### 4. Verify

```bash
# List tasks
curl http://localhost:8000/api/tasks

# Create a task
curl -X POST http://localhost:8000/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Buy milk", "description": "From the store"}'

# Get a task
curl http://localhost:8000/api/tasks/1

# Update a task
curl -X PUT http://localhost:8000/api/tasks/1 \
  -H 'Content-Type: application/json' \
  -d '{"done": true}'

# Delete a task
curl -X DELETE http://localhost:8000/api/tasks/2
```

Connect from any MCP client (e.g., Claude Desktop) using `http://127.0.0.1:9090`.

### 5. Explorer (optional)

The MCP server includes a built-in Tool Explorer UI:

> **Security:** The Explorer exposes module schemas and execution via unauthenticated HTTP.
> Only enable in **development/staging**. Do NOT enable in production without adding your own auth layer.

Browse to `http://127.0.0.1:9090/explorer/` for the interactive module explorer with Try-it execution.

#### Example payloads for Try-it

The demo ships with 2 seed tasks (id 1 and 2). Use these example inputs in the explorer:

| Module | Example input |
|---|---|
| `task_stats.v1` | *(no input required)* |
| `api.tasks.list` | *(no input required)* |
| `api.tasks.get` | `{"task_id": 1}` |
| `api.tasks.create` | `{"title": "Buy milk", "description": "From the store", "done": false}` |
| `api.tasks.update` | `{"task_id": 1, "title": "Try django-apcore (done!)", "done": true}` |
| `api.tasks.delete` | `{"task_id": 2}` |

### 6. Output Formatting (optional)

By default, MCP results are raw JSON. To get Markdown-formatted output:

```python
# In settings.py
APCORE_OUTPUT_FORMATTER = "apcore_toolkit.to_markdown"
```

Or via CLI:

```bash
python manage.py apcore_serve --output-formatter apcore_toolkit.to_markdown ...
```

### 7. JWT Authentication (optional)

Enable JWT-based authentication on the MCP server (requires apcore-mcp >= 0.10.0). When enabled, clients must send a valid `Authorization: Bearer <token>` header.

Uncomment the `APCORE_JWT_*` lines in `demo/settings.py`, then restart the MCP server:

```bash
python manage.py apcore_serve --transport streamable-http --host 127.0.0.1 --port 9090 --jwt-secret "demo-jwt-secret"
```

Generate a test token:

```bash
python -c "import jwt; print(jwt.encode({'sub': 'demo-user', 'roles': ['admin']}, 'demo-jwt-secret', algorithm='HS256'))"
```

## Docker

```bash
cd example
docker compose up --build
```

This starts two services:

| Service | URL | Description |
|---|---|---|
| `web` | http://localhost:8000 | Django API server |
| `mcp` | http://localhost:9090 | MCP server (scan → serve via `entrypoint.sh`) |

```bash
# Cleanup
docker compose down
```

## Running Tests

```bash
cd example
python -m pytest tests/ -v
```

## Features Demonstrated

- **`DjangoApcore` unified API** — Single import for all django-apcore functionality
- **Route scanning** — `apcore_scan --source ninja` discovers all 5 CRUD routes
- **Output formats** — `--output yaml`, `--output python`, or `--output registry`
- **Output verification** — `--verify` validates generated files
- **Semantic module IDs** — action verbs from function names (`list`, `get`, `create`, `update`, `delete`)
- **`$ref` resolution** — Pydantic model schemas resolved from OpenAPI `$ref` references
- **Annotation inference** — GET→readonly/cacheable, DELETE→destructive, PUT→idempotent
- **Pydantic schemas** — Input validation from `TaskCreate` and `TaskUpdate` models
- **`@app.module()` decorator** — `task_stats.v1` registered via `DjangoApcore`
- **MCP Tool Explorer** — Browser-based module viewer via `apcore_serve --explorer`
- **MCP server** — Streamable HTTP transport on port 9090
- **Output formatting** — Optional Markdown via `APCORE_OUTPUT_FORMATTER`
- **Observability** — Tracing (stdout), metrics, and structured JSON logging
- **Input validation** — `--validate-inputs` checks tool inputs against schemas
- **JWT authentication** — Optional Bearer token auth via `APCORE_JWT_SECRET`

## Project Structure

```
example/
├── Dockerfile              # Python 3.11 image with django-apcore installed
├── docker-compose.yml      # web + mcp services
├── entrypoint.sh           # scan → serve pipeline
├── .env.example            # Environment variable template
├── manage.py               # Django manage.py
├── conftest.py             # pytest-django configuration
├── demo/
│   ├── settings.py         # Django settings with apcore config
│   ├── urls.py             # API route (django-ninja)
│   ├── api.py              # Task Manager CRUD with Pydantic schemas
│   └── apcore_modules/
│       ├── __init__.py     # Re-exports for auto-discovery
│       ├── task_stats.py   # @app.module() via DjangoApcore
│       └── *.binding.yaml  # Auto-generated YAML bindings for scanned routes
└── tests/
    └── test_demo.py        # Unit + integration + DjangoApcore tests
```

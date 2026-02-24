# django-apcore Docker Demo

A self-contained Docker demo showcasing django-apcore's core features: `@module` decorator, `executor_call()` from views, MCP server via `apcore_serve`, and async tasks.

## Quick Start

```bash
cd example
docker compose up --build
```

This starts two services:

| Service | URL | Description |
|---------|-----|-------------|
| `web` | http://localhost:8000 | Django API server |
| `mcp` | http://localhost:9090 | MCP server (`apcore_serve`) |

## Registered Modules

| Module ID | Function | Description |
|-----------|----------|-------------|
| `hello` | `hello_world(name)` | Greet someone by name |
| `math.add` | `add(a, b)` | Add two numbers |
| `math.multiply` | `multiply(a, b)` | Multiply two numbers |
| `slow.process` | `slow_process(seconds)` | Simulate a long-running task |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hello/` | Call the hello module |
| POST | `/api/add/` | Add two numbers |
| POST | `/api/multiply/` | Multiply two numbers |
| POST | `/api/tasks/submit/` | Submit an async task |
| GET | `/api/tasks/<task_id>/status/` | Poll task status |
| GET | `/api/modules/` | List registered module count |

## curl Examples

```bash
# Hello (default)
curl http://localhost:8000/api/hello/

# Hello with name
curl http://localhost:8000/api/hello/?name=Django

# Add
curl -X POST http://localhost:8000/api/add/ \
  -H 'Content-Type: application/json' \
  -d '{"a": 10, "b": 32}'

# Multiply
curl -X POST http://localhost:8000/api/multiply/ \
  -H 'Content-Type: application/json' \
  -d '{"a": 7, "b": 6}'

# Submit async task
curl -X POST http://localhost:8000/api/tasks/submit/ \
  -H 'Content-Type: application/json' \
  -d '{"module_id": "slow.process", "inputs": {"seconds": 3}}'

# Poll task status (replace <task_id> with the returned task_id)
curl http://localhost:8000/api/tasks/<task_id>/status/

# List modules
curl http://localhost:8000/api/modules/
```

## MCP Server

The MCP server runs on port 9090 using the `streamable-http` transport. Connect your MCP-compatible AI agent to `http://localhost:9090` to discover and call the registered modules.

## Project Structure

```
example/
├── Dockerfile              # Python 3.11 image with django-apcore installed
├── docker-compose.yml      # web + mcp services
├── manage.py               # Django manage.py
├── demo/
│   ├── settings.py         # Django settings with apcore config
│   ├── urls.py             # API route definitions
│   ├── views.py            # Views using executor_call() and submit_task()
│   └── apcore_modules/
│       ├── __init__.py     # Re-exports for auto-discovery
│       ├── hello.py        # @module "hello"
│       ├── math_tools.py   # @module "math.add", "math.multiply"
│       └── slow_task.py    # @module "slow.process"
└── README.md
```

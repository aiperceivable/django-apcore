"""Task Manager API — django-apcore demo application.

Demonstrates:
- django-ninja CRUD routes with Pydantic schemas
- Automatic route scanning via NinjaScanner
- @module decorator for standalone modules
- MCP server via streamable-http transport
"""

from __future__ import annotations

from ninja import NinjaAPI, Schema
from ninja.errors import HttpError

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class TaskCreate(Schema):
    title: str
    description: str = ""
    done: bool = False


class TaskUpdate(Schema):
    title: str | None = None
    description: str | None = None
    done: bool | None = None


class Task(Schema):
    id: int
    title: str
    description: str
    done: bool


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_tasks: dict[int, dict] = {
    1: {
        "id": 1,
        "title": "Try django-apcore",
        "description": "Run the demo",
        "done": False,
    },
    2: {
        "id": 2,
        "title": "Connect MCP client",
        "description": "Use Claude Desktop",
        "done": False,
    },
}
_next_id: int = 3


# ---------------------------------------------------------------------------
# django-ninja API
# ---------------------------------------------------------------------------

api = NinjaAPI()


@api.get("/tasks", response=list[Task])
def list_tasks(request):
    """List all tasks."""
    return list(_tasks.values())


@api.post("/tasks", response={201: Task})
def create_task(request, body: TaskCreate):
    """Create a new task."""
    global _next_id
    task = {
        "id": _next_id,
        "title": body.title,
        "description": body.description,
        "done": body.done,
    }
    _tasks[_next_id] = task
    _next_id += 1
    return 201, task


@api.get("/tasks/{task_id}", response=Task)
def get_task(request, task_id: int):
    """Get a task by its ID."""
    task = _tasks.get(task_id)
    if task is None:
        raise HttpError(404, "not found")
    return task


@api.put("/tasks/{task_id}", response=Task)
def update_task(request, task_id: int, body: TaskUpdate):
    """Update an existing task."""
    task = _tasks.get(task_id)
    if task is None:
        raise HttpError(404, "not found")
    if body.title is not None:
        task["title"] = body.title
    if body.description is not None:
        task["description"] = body.description
    if body.done is not None:
        task["done"] = body.done
    return task


@api.delete("/tasks/{task_id}")
def delete_task(request, task_id: int):
    """Delete a task permanently."""
    if task_id not in _tasks:
        raise HttpError(404, "not found")
    del _tasks[task_id]
    return {"deleted": True}

"""Standalone module example using the DjangoApcore unified entry point.

Demonstrates registering a custom module via ``app.module()`` decorator
and using ``ModuleAnnotations`` for behavioral hints.
"""

from apcore import ModuleAnnotations

from demo.api import _tasks
from django_apcore import DjangoApcore

app = DjangoApcore.get_instance()


@app.module(
    id="task_stats.v1",
    description="Return summary statistics about all tasks.",
    tags=["analytics"],
    annotations=ModuleAnnotations(readonly=True, cacheable=True),
)
def task_stats() -> dict:
    """Return summary statistics about all tasks.

    Counts total, done, and pending tasks from the in-memory store.
    """
    total = len(_tasks)
    done = sum(1 for t in _tasks.values() if t["done"])
    return {"total": total, "done": done, "pending": total - done}

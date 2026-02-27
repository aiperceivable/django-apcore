from apcore import module

from demo.api import _tasks


@module(id="task_stats.v1")
def task_stats() -> dict:
    """Return summary statistics about all tasks."""
    total = len(_tasks)
    done = sum(1 for t in _tasks.values() if t["done"])
    return {"total": total, "done": done, "pending": total - done}

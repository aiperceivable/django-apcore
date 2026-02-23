"""AsyncTaskManager Django integration.

Provides a process-level singleton AsyncTaskManager configured from
APCORE_TASK_* Django settings.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger("django_apcore")

_task_manager: Any = None
_task_lock = threading.Lock()


def get_task_manager() -> Any:
    """Return the singleton AsyncTaskManager for this Django process.

    Lazily created on first call. Configured from APCORE_TASK_MAX_CONCURRENT
    and APCORE_TASK_MAX_TASKS settings.

    Returns:
        apcore.AsyncTaskManager instance.
    """
    global _task_manager
    if _task_manager is None:
        with _task_lock:
            if _task_manager is None:
                from apcore import AsyncTaskManager

                from django_apcore.registry import get_executor
                from django_apcore.settings import get_apcore_settings

                settings = get_apcore_settings()
                _task_manager = AsyncTaskManager(
                    executor=get_executor(),
                    max_concurrent=settings.task_max_concurrent,
                    max_tasks=settings.task_max_tasks,
                )
                logger.debug(
                    "Created AsyncTaskManager (max_concurrent=%d, max_tasks=%d)",
                    settings.task_max_concurrent,
                    settings.task_max_tasks,
                )
    return _task_manager


def _reset_task_manager() -> None:
    """Reset the singleton task manager. For testing only."""
    global _task_manager
    with _task_lock:
        if _task_manager is not None:
            # Attempt graceful shutdown if possible
            import asyncio

            try:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop is not None and loop.is_running():
                    loop.create_task(_task_manager.shutdown())
                else:
                    loop = asyncio.new_event_loop()
                    try:
                        loop.run_until_complete(_task_manager.shutdown())
                    finally:
                        loop.close()
            except Exception:
                pass
        _task_manager = None

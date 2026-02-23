"""Management command for async task management.

Usage:
    manage.py apcore_tasks list [--status STATUS]
    manage.py apcore_tasks cancel TASK_ID
    manage.py apcore_tasks cleanup [--max-age SECONDS]
"""

from __future__ import annotations

import asyncio
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_apcore.tasks import get_task_manager

try:
    from apcore import TaskStatus
except ImportError:  # pragma: no cover
    TaskStatus = None  # type: ignore[assignment,misc]


class Command(BaseCommand):
    help = "Manage apcore async tasks (list, cancel, cleanup)"

    def add_arguments(self, parser: Any) -> None:
        subparsers = parser.add_subparsers(dest="subcommand")

        # list
        list_parser = subparsers.add_parser("list", help="List tasks")
        list_parser.add_argument(
            "--status",
            choices=["pending", "running", "completed", "failed", "cancelled"],
            default=None,
            help="Filter by status",
        )

        # cancel
        cancel_parser = subparsers.add_parser("cancel", help="Cancel a task")
        cancel_parser.add_argument("task_id", help="Task ID to cancel")

        # cleanup
        cleanup_parser = subparsers.add_parser(
            "cleanup", help="Clean up completed tasks"
        )
        cleanup_parser.add_argument(
            "--max-age",
            type=int,
            default=3600,
            help="Max age in seconds for completed tasks (default: 3600)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        subcommand = options.get("subcommand")
        if not subcommand:
            raise CommandError(
                "Subcommand required: list, cancel, or cleanup"
            )

        tm = get_task_manager()

        if subcommand == "list":
            self._handle_list(tm, options)
        elif subcommand == "cancel":
            self._handle_cancel(tm, options)
        elif subcommand == "cleanup":
            self._handle_cleanup(tm, options)

    def _handle_list(self, tm: Any, options: dict) -> None:
        status_filter = options.get("status")
        if status_filter and TaskStatus is not None:
            status_filter = TaskStatus[status_filter.upper()]
        tasks = tm.list_tasks(status=status_filter)
        if not tasks:
            self.stdout.write("No tasks found.")
            return
        for task in tasks:
            self.stdout.write(
                f"  {task.task_id}  {task.module_id}  {task.status.value}"
            )

    def _handle_cancel(self, tm: Any, options: dict) -> None:
        task_id = options["task_id"]
        result = asyncio.run(tm.cancel(task_id))
        if result:
            self.stdout.write(f"Task {task_id} cancelled.")
        else:
            self.stdout.write(f"Task {task_id} could not be cancelled.")

    def _handle_cleanup(self, tm: Any, options: dict) -> None:
        max_age = options.get("max_age", 3600)
        count = tm.cleanup(max_age_seconds=max_age)
        self.stdout.write(f"Cleaned up {count} tasks.")

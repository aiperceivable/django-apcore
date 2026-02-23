# tests/test_commands.py
"""Tests for the apcore_scan and apcore_tasks management commands."""

from __future__ import annotations

import re
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.core.management import CommandError, call_command

SCAN_CMD = "django_apcore.management.commands.apcore_scan"
TASKS_CMD = "django_apcore.management.commands.apcore_tasks"


class TestApCoreScanCommand:
    """Test the apcore_scan management command."""

    def test_command_exists(self):
        """apcore_scan command is discoverable by Django."""
        from django.core.management import get_commands

        commands = get_commands()
        assert "apcore_scan" in commands

    def test_source_required(self):
        """--source is a required argument."""
        with pytest.raises((CommandError, SystemExit)):
            call_command("apcore_scan")

    def test_source_ninja_accepted(self):
        """--source ninja is a valid choice."""
        with patch(f"{SCAN_CMD}.get_scanner") as mock_get:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner.get_source_name.return_value = "django-ninja"
            mock_get.return_value = mock_scanner

            out = StringIO()
            call_command("apcore_scan", "--source", "ninja", stdout=out)

    def test_source_drf_accepted(self):
        """--source drf is a valid choice."""
        with patch(f"{SCAN_CMD}.get_scanner") as mock_get:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner.get_source_name.return_value = "drf-spectacular"
            mock_get.return_value = mock_scanner

            out = StringIO()
            call_command("apcore_scan", "--source", "drf", stdout=out)

    def test_source_invalid_rejected(self):
        """Invalid --source values are rejected."""
        with pytest.raises((CommandError, SystemExit)):
            call_command("apcore_scan", "--source", "graphql")

    def test_output_yaml_default(self):
        """Default --output is yaml."""
        with (
            patch(f"{SCAN_CMD}.get_scanner") as mock_get,
            patch(f"{SCAN_CMD}.get_writer") as mock_writer_get,
        ):
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner.get_source_name.return_value = "test"
            mock_get.return_value = mock_scanner

            mock_writer = MagicMock()
            mock_writer.write.return_value = []
            mock_writer_get.return_value = mock_writer

            call_command("apcore_scan", "--source", "ninja")
            mock_writer_get.assert_called_once_with("yaml")

    def test_output_python_accepted(self):
        """--output python is a valid choice."""
        with (
            patch(f"{SCAN_CMD}.get_scanner") as mock_get,
            patch(f"{SCAN_CMD}.get_writer") as mock_writer_get,
        ):
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner.get_source_name.return_value = "test"
            mock_get.return_value = mock_scanner

            mock_writer = MagicMock()
            mock_writer.write.return_value = []
            mock_writer_get.return_value = mock_writer

            call_command("apcore_scan", "--source", "ninja", "--output", "python")
            mock_writer_get.assert_called_once_with("python")

    def test_output_invalid_rejected(self):
        """Invalid --output values are rejected."""
        with pytest.raises((CommandError, SystemExit)):
            call_command("apcore_scan", "--source", "ninja", "--output", "json")

    def test_dry_run_flag(self):
        """--dry-run prevents file writing."""
        with (
            patch(f"{SCAN_CMD}.get_scanner") as mock_get,
            patch(f"{SCAN_CMD}.get_writer") as mock_writer_get,
        ):
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner.get_source_name.return_value = "test"
            mock_get.return_value = mock_scanner

            mock_writer = MagicMock()
            mock_writer.write.return_value = []
            mock_writer_get.return_value = mock_writer

            call_command("apcore_scan", "--source", "ninja", "--dry-run")
            mock_writer.write.assert_called_once()
            # dry_run should be passed as True
            _, kwargs = mock_writer.write.call_args
            assert kwargs.get("dry_run") is True

    def test_include_pattern_passed_to_scanner(self):
        """--include pattern is forwarded to scanner.scan()."""
        with (
            patch(f"{SCAN_CMD}.get_scanner") as mock_get,
            patch(f"{SCAN_CMD}.get_writer") as mock_writer_get,
        ):
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner.get_source_name.return_value = "test"
            mock_get.return_value = mock_scanner

            mock_writer = MagicMock()
            mock_writer.write.return_value = []
            mock_writer_get.return_value = mock_writer

            call_command(
                "apcore_scan",
                "--source",
                "ninja",
                "--include",
                "users.*",
            )
            mock_scanner.scan.assert_called_once_with(include="users.*", exclude=None)

    def test_exclude_pattern_passed_to_scanner(self):
        """--exclude pattern is forwarded to scanner.scan()."""
        with (
            patch(f"{SCAN_CMD}.get_scanner") as mock_get,
            patch(f"{SCAN_CMD}.get_writer") as mock_writer_get,
        ):
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner.get_source_name.return_value = "test"
            mock_get.return_value = mock_scanner

            mock_writer = MagicMock()
            mock_writer.write.return_value = []
            mock_writer_get.return_value = mock_writer

            call_command(
                "apcore_scan",
                "--source",
                "ninja",
                "--exclude",
                "admin.*",
            )
            mock_scanner.scan.assert_called_once_with(include=None, exclude="admin.*")

    def test_invalid_include_regex_rejected(self):
        """Invalid --include regex pattern raises CommandError."""
        with patch(f"{SCAN_CMD}.get_scanner") as mock_get:
            mock_scanner = MagicMock()
            mock_scanner.get_source_name.return_value = "test"
            mock_scanner.scan.side_effect = re.error("bad pattern")
            mock_get.return_value = mock_scanner

            with pytest.raises(CommandError, match="Invalid.*pattern"):
                call_command(
                    "apcore_scan",
                    "--source",
                    "ninja",
                    "--include",
                    "[invalid",
                )

    def test_output_prefix(self):
        """Command output uses [django-apcore] prefix."""
        with (
            patch(f"{SCAN_CMD}.get_scanner") as mock_get,
            patch(f"{SCAN_CMD}.get_writer") as mock_writer_get,
        ):
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner.get_source_name.return_value = "test"
            mock_get.return_value = mock_scanner

            mock_writer = MagicMock()
            mock_writer.write.return_value = []
            mock_writer_get.return_value = mock_writer

            out = StringIO()
            call_command("apcore_scan", "--source", "ninja", stdout=out)
            output = out.getvalue()
            assert "[django-apcore]" in output

    def test_dir_from_settings_default(self):
        """--dir defaults to APCORE_MODULE_DIR setting."""
        with (
            patch(f"{SCAN_CMD}.get_scanner") as mock_get,
            patch(f"{SCAN_CMD}.get_writer") as mock_writer_get,
            patch(f"{SCAN_CMD}.get_apcore_settings") as mock_settings,
        ):
            mock_settings.return_value = MagicMock(module_dir="custom_dir/")

            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner.get_source_name.return_value = "test"
            mock_get.return_value = mock_scanner

            mock_writer = MagicMock()
            mock_writer.write.return_value = []
            mock_writer_get.return_value = mock_writer

            call_command("apcore_scan", "--source", "ninja")
            args, kwargs = mock_writer.write.call_args
            assert "custom_dir/" in args or kwargs.get("output_dir") == "custom_dir/"

    def test_scanner_import_error_becomes_command_error(self):
        """ImportError from scanner becomes CommandError with install instructions."""
        with patch(f"{SCAN_CMD}.get_scanner") as mock_get:
            mock_get.side_effect = ImportError(
                "django-ninja is required for --source ninja."
            )
            with pytest.raises(CommandError, match="django-ninja is required"):
                call_command("apcore_scan", "--source", "ninja")

    def test_zero_endpoints_message(self):
        """When no endpoints found, display informative message and exit 0."""
        with (
            patch(f"{SCAN_CMD}.get_scanner") as mock_get,
            patch(f"{SCAN_CMD}.get_writer") as mock_writer_get,
        ):
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner.get_source_name.return_value = "django-ninja"
            mock_get.return_value = mock_scanner

            mock_writer = MagicMock()
            mock_writer.write.return_value = []
            mock_writer_get.return_value = mock_writer

            out = StringIO()
            call_command("apcore_scan", "--source", "ninja", stdout=out)
            output = out.getvalue()
            assert "No endpoints found" in output or "0" in output


class TestApcoreTasksCommand:
    """Test the apcore_tasks management command."""

    def test_command_exists(self):
        """apcore_tasks command is discoverable by Django."""
        from django.core.management import get_commands

        commands = get_commands()
        assert "apcore_tasks" in commands

    def test_no_subcommand_raises_error(self):
        """Missing subcommand raises CommandError."""
        with patch(f"{TASKS_CMD}.get_task_manager"):
            with pytest.raises(CommandError, match="Subcommand required"):
                call_command("apcore_tasks")

    def test_list_no_tasks(self):
        """list subcommand with no tasks prints 'No tasks found.'."""
        with patch(f"{TASKS_CMD}.get_task_manager") as mock_gtm:
            mock_tm = MagicMock()
            mock_tm.list_tasks.return_value = []
            mock_gtm.return_value = mock_tm
            out = StringIO()
            call_command("apcore_tasks", "list", stdout=out)
            assert "No tasks" in out.getvalue()

    def test_list_with_tasks(self):
        """list subcommand displays task_id, module_id, and status."""
        with patch(f"{TASKS_CMD}.get_task_manager") as mock_gtm:
            mock_task = MagicMock()
            mock_task.task_id = "abc-123"
            mock_task.module_id = "test.module"
            mock_task.status.value = "running"
            mock_tm = MagicMock()
            mock_tm.list_tasks.return_value = [mock_task]
            mock_gtm.return_value = mock_tm
            out = StringIO()
            call_command("apcore_tasks", "list", stdout=out)
            output = out.getvalue()
            assert "abc-123" in output
            assert "test.module" in output

    def test_list_with_status_filter(self):
        """list --status passes a TaskStatus enum to list_tasks."""
        with (
            patch(f"{TASKS_CMD}.get_task_manager") as mock_gtm,
            patch(f"{TASKS_CMD}.TaskStatus") as mock_ts_cls,
        ):
            mock_tm = MagicMock()
            mock_tm.list_tasks.return_value = []
            mock_gtm.return_value = mock_tm
            mock_ts_cls.__getitem__ = MagicMock(return_value="RUNNING")
            out = StringIO()
            call_command("apcore_tasks", "list", "--status", "running", stdout=out)
            mock_ts_cls.__getitem__.assert_called_once_with("RUNNING")
            mock_tm.list_tasks.assert_called_once_with(status="RUNNING")

    def test_cleanup(self):
        """cleanup subcommand calls tm.cleanup with --max-age value."""
        with patch(f"{TASKS_CMD}.get_task_manager") as mock_gtm:
            mock_tm = MagicMock()
            mock_tm.cleanup.return_value = 5
            mock_gtm.return_value = mock_tm
            out = StringIO()
            call_command("apcore_tasks", "cleanup", "--max-age", "1800", stdout=out)
            mock_tm.cleanup.assert_called_once_with(max_age_seconds=1800)
            assert "5" in out.getvalue()

    def test_cleanup_default_max_age(self):
        """cleanup subcommand defaults to max_age=3600."""
        with patch(f"{TASKS_CMD}.get_task_manager") as mock_gtm:
            mock_tm = MagicMock()
            mock_tm.cleanup.return_value = 0
            mock_gtm.return_value = mock_tm
            out = StringIO()
            call_command("apcore_tasks", "cleanup", stdout=out)
            mock_tm.cleanup.assert_called_once_with(max_age_seconds=3600)

    def test_cancel_success(self):
        """cancel subcommand reports success when tm.cancel returns True."""
        with patch(f"{TASKS_CMD}.get_task_manager") as mock_gtm:
            mock_tm = MagicMock()
            mock_tm.cancel = AsyncMock(return_value=True)
            mock_gtm.return_value = mock_tm
            out = StringIO()
            call_command("apcore_tasks", "cancel", "task-123", stdout=out)
            assert "cancelled" in out.getvalue().lower()

    def test_cancel_failure(self):
        """cancel subcommand reports failure when tm.cancel returns False."""
        with patch(f"{TASKS_CMD}.get_task_manager") as mock_gtm:
            mock_tm = MagicMock()
            mock_tm.cancel = AsyncMock(return_value=False)
            mock_gtm.return_value = mock_tm
            out = StringIO()
            call_command("apcore_tasks", "cancel", "task-456", stdout=out)
            assert "could not be cancelled" in out.getvalue().lower()

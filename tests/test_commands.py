# tests/test_commands.py
"""Tests for the apcore_scan management command."""

from __future__ import annotations

import re
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import CommandError, call_command

SCAN_CMD = "django_apcore.management.commands.apcore_scan"


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

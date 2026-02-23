# Task 009: apcore_scan Management Command

## Goal

Implement the `apcore_scan` Django management command that orchestrates the scan-and-write workflow. It parses arguments (`--source`, `--output`, `--dir`, `--dry-run`, `--include`, `--exclude`, `--validate`), validates them per Section 7.3 of the tech-design, instantiates the appropriate scanner and writer, runs the scan, and writes output. All output uses the `[django-apcore]` prefix and respects verbosity levels.

## Files Involved

### Create

- `src/django_apcore/management/__init__.py` -- Package init (empty)
- `src/django_apcore/management/commands/__init__.py` -- Package init (empty)
- `src/django_apcore/management/commands/apcore_scan.py` -- `Command` class

### Test

- `tests/test_commands.py` -- Unit tests for apcore_scan command arguments, validation, and orchestration

## Steps

### Step 1: Write tests (TDD -- Red phase)

Create `tests/test_commands.py`:

```python
# tests/test_commands.py
import pytest
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command, CommandError


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
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner.get_source_name.return_value = "django-ninja"
            mock_get.return_value = mock_scanner

            out = StringIO()
            call_command("apcore_scan", "--source", "ninja", stdout=out)

    def test_source_drf_accepted(self):
        """--source drf is a valid choice."""
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
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
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
            with patch("django_apcore.management.commands.apcore_scan.get_writer") as mock_writer_get:
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
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
            with patch("django_apcore.management.commands.apcore_scan.get_writer") as mock_writer_get:
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
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
            with patch("django_apcore.management.commands.apcore_scan.get_writer") as mock_writer_get:
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
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
            with patch("django_apcore.management.commands.apcore_scan.get_writer") as mock_writer_get:
                mock_scanner = MagicMock()
                mock_scanner.scan.return_value = []
                mock_scanner.get_source_name.return_value = "test"
                mock_get.return_value = mock_scanner

                mock_writer = MagicMock()
                mock_writer.write.return_value = []
                mock_writer_get.return_value = mock_writer

                call_command("apcore_scan", "--source", "ninja", "--include", "users.*")
                mock_scanner.scan.assert_called_once_with(
                    include="users.*", exclude=None
                )

    def test_exclude_pattern_passed_to_scanner(self):
        """--exclude pattern is forwarded to scanner.scan()."""
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
            with patch("django_apcore.management.commands.apcore_scan.get_writer") as mock_writer_get:
                mock_scanner = MagicMock()
                mock_scanner.scan.return_value = []
                mock_scanner.get_source_name.return_value = "test"
                mock_get.return_value = mock_scanner

                mock_writer = MagicMock()
                mock_writer.write.return_value = []
                mock_writer_get.return_value = mock_writer

                call_command("apcore_scan", "--source", "ninja", "--exclude", "admin.*")
                mock_scanner.scan.assert_called_once_with(
                    include=None, exclude="admin.*"
                )

    def test_invalid_include_regex_rejected(self):
        """Invalid --include regex pattern raises CommandError."""
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
            mock_scanner = MagicMock()
            mock_scanner.get_source_name.return_value = "test"
            import re
            mock_scanner.scan.side_effect = re.error("bad pattern")
            mock_get.return_value = mock_scanner

            with pytest.raises(CommandError, match="Invalid.*pattern"):
                call_command("apcore_scan", "--source", "ninja", "--include", "[invalid")

    def test_output_prefix(self):
        """Command output uses [django-apcore] prefix."""
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
            with patch("django_apcore.management.commands.apcore_scan.get_writer") as mock_writer_get:
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
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
            with patch("django_apcore.management.commands.apcore_scan.get_writer") as mock_writer_get:
                with patch("django_apcore.management.commands.apcore_scan.get_apcore_settings") as mock_settings:
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
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
            mock_get.side_effect = ImportError(
                "django-ninja is required for --source ninja."
            )
            with pytest.raises(CommandError, match="django-ninja is required"):
                call_command("apcore_scan", "--source", "ninja")

    def test_zero_endpoints_message(self):
        """When no endpoints found, display informative message and exit 0."""
        with patch("django_apcore.management.commands.apcore_scan.get_scanner") as mock_get:
            with patch("django_apcore.management.commands.apcore_scan.get_writer") as mock_writer_get:
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
```

### Step 2: Run tests -- verify they fail

```bash
pytest tests/test_commands.py::TestApCoreScanCommand -x --tb=short
```

Expected: `ModuleNotFoundError` or `CommandError` because the management command does not exist yet.

### Step 3: Implement

Create `src/django_apcore/management/__init__.py` and `src/django_apcore/management/commands/__init__.py` (empty files, created in task 001).

Create `src/django_apcore/management/commands/apcore_scan.py`:

```python
"""apcore_scan management command.

Orchestrates scanning of Django API endpoints and writing output files.

Usage:
    manage.py apcore_scan --source ninja --output yaml
    manage.py apcore_scan --source drf --output python --dir ./modules/
    manage.py apcore_scan --source ninja --dry-run --include "users.*"
"""

from __future__ import annotations

import re

from django.core.management.base import BaseCommand, CommandError

from django_apcore.output import get_writer
from django_apcore.scanners import get_scanner
from django_apcore.settings import get_apcore_settings


class Command(BaseCommand):
    help = "Scan Django API endpoints and generate apcore module definitions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source", "-s",
            type=str,
            required=True,
            choices=["ninja", "drf"],
            help="Scanner source: 'ninja' for django-ninja, 'drf' for DRF via drf-spectacular.",
        )
        parser.add_argument(
            "--output", "-o",
            type=str,
            default="yaml",
            choices=["yaml", "python"],
            help="Output format: 'yaml' for .binding.yaml files, 'python' for @module files. Default: yaml.",
        )
        parser.add_argument(
            "--dir", "-d",
            type=str,
            default=None,
            help="Output directory. Default: APCORE_MODULE_DIR setting.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Preview output without writing files.",
        )
        parser.add_argument(
            "--include",
            type=str,
            default=None,
            help="Regex pattern to include (matches against endpoint path).",
        )
        parser.add_argument(
            "--exclude",
            type=str,
            default=None,
            help="Regex pattern to exclude.",
        )
        parser.add_argument(
            "--validate",
            action="store_true",
            default=False,
            help="Validate generated schemas against apcore spec.",
        )

    def handle(self, *args, **options):
        source = options["source"]
        output_format = options["output"]
        output_dir = options["dir"]
        dry_run = options["dry_run"]
        include = options["include"]
        exclude = options["exclude"]
        validate = options["validate"]
        verbosity = options["verbosity"]

        # Validate regex patterns
        if include:
            try:
                re.compile(include)
            except re.error as e:
                raise CommandError(
                    f"Invalid --include pattern: '{include}'. Must be valid regex. Error: {e}"
                )

        if exclude:
            try:
                re.compile(exclude)
            except re.error as e:
                raise CommandError(
                    f"Invalid --exclude pattern: '{exclude}'. Must be valid regex. Error: {e}"
                )

        # Resolve output directory
        if output_dir is None:
            settings = get_apcore_settings()
            output_dir = settings.module_dir

        # Get scanner
        try:
            scanner = get_scanner(source)
        except ImportError as e:
            raise CommandError(str(e))
        except ValueError as e:
            raise CommandError(str(e))

        # Run scan
        source_name = scanner.get_source_name()
        if verbosity >= 1:
            self.stdout.write(
                f"[django-apcore] Scanning {source_name} endpoints..."
            )

        try:
            modules = scanner.scan(include=include, exclude=exclude)
        except ImportError as e:
            raise CommandError(str(e))
        except re.error as e:
            raise CommandError(
                f"Invalid --include or --exclude pattern. Must be valid regex. Error: {e}"
            )

        if verbosity >= 1:
            self.stdout.write(
                f"[django-apcore] Found {len(modules)} endpoints."
            )

        if not modules:
            self.stdout.write(
                f"[django-apcore] No endpoints found for source '{source}'. "
                f"Ensure your API is configured."
            )
            return

        # Report warnings
        all_warnings = []
        for module in modules:
            all_warnings.extend(module.warnings)
        if all_warnings and verbosity >= 1:
            self.stdout.write(f"[django-apcore] Warnings: {len(all_warnings)}")
            if verbosity >= 2:
                for warning in all_warnings:
                    self.stdout.write(f"[django-apcore]   - {warning}")

        # Get writer and write output
        writer = get_writer(output_format)

        if dry_run:
            if verbosity >= 1:
                self.stdout.write("[django-apcore] Dry run -- no files written.")
            result = writer.write(modules, output_dir, dry_run=True)
            if verbosity >= 2:
                for item in result:
                    self.stdout.write(f"[django-apcore] Would write: {item}")
        else:
            result = writer.write(modules, output_dir, dry_run=False)
            if verbosity >= 1:
                self.stdout.write(
                    f"[django-apcore] Generated {len(modules)} module definitions."
                )
                self.stdout.write(
                    f"[django-apcore] Written {len(result)} files to {output_dir}/"
                )
```

### Step 4: Run tests -- verify they pass

```bash
pytest tests/test_commands.py::TestApCoreScanCommand -x --tb=short -v
```

All tests should pass.

### Step 5: Commit

```bash
git add src/django_apcore/management/ tests/test_commands.py
git commit -m "feat: apcore_scan management command with argument validation"
```

## Acceptance Criteria

- [ ] `manage.py apcore_scan` is discoverable by Django's management command system
- [ ] `--source` is required; accepts `ninja` and `drf` only
- [ ] `--output` defaults to `yaml`; accepts `yaml` and `python` only
- [ ] `--dir` defaults to `APCORE_MODULE_DIR` from settings
- [ ] `--dry-run` flag prevents file writing but still runs scan
- [ ] `--include` and `--exclude` patterns forwarded to scanner
- [ ] Invalid regex patterns raise `CommandError` with descriptive message
- [ ] Missing optional dependency (django-ninja / drf-spectacular) raises `CommandError` with install instructions
- [ ] Zero endpoints produces informative message and exits with code 0
- [ ] All output uses `[django-apcore]` prefix
- [ ] Verbosity levels 0/1/2 control output detail
- [ ] 90% test coverage for `apcore_scan.py`

## Dependencies

- **005-scanner-base** -- Requires `BaseScanner`, `ScannedModule`, `get_scanner()`
- **006-output-writers** -- Requires `YAMLWriter`, `PythonWriter`, `get_writer()`

## Estimated Time

4 hours

## Troubleshooting

**Issue: `call_command("apcore_scan")` raises `SystemExit` instead of `CommandError`**
Django's `argparse` integration raises `SystemExit` for missing required arguments. In tests, catch both `CommandError` and `SystemExit`: `with pytest.raises((CommandError, SystemExit))`.

**Issue: Command not found in `get_commands()`**
Ensure `src/django_apcore/management/commands/` directory has `__init__.py` files at both the `management/` and `commands/` levels. Also ensure `"django_apcore"` is in `INSTALLED_APPS` in the test conftest.

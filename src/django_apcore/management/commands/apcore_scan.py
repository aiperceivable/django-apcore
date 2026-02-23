"""apcore_scan management command.

Orchestrates scanning of Django API endpoints and writing output files.

Usage:
    manage.py apcore_scan --source ninja --output yaml
    manage.py apcore_scan --source drf --output python --dir ./modules/
    manage.py apcore_scan --source ninja --dry-run --include "users.*"
"""

from __future__ import annotations

import re
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_apcore.output import get_writer
from django_apcore.scanners import get_scanner
from django_apcore.settings import get_apcore_settings


class Command(BaseCommand):
    help = "Scan Django API endpoints and generate apcore module definitions."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--source",
            "-s",
            type=str,
            required=True,
            choices=["ninja", "drf"],
            help=(
                "Scanner source: 'ninja' for django-ninja, "
                "'drf' for DRF via drf-spectacular."
            ),
        )
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            default="yaml",
            choices=["yaml", "python"],
            help=(
                "Output format: 'yaml' for .binding.yaml files, "
                "'python' for @module files. Default: yaml."
            ),
        )
        parser.add_argument(
            "--dir",
            "-d",
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

    def handle(self, *args: Any, **options: Any) -> None:
        source = options["source"]
        output_format = options["output"]
        output_dir = options["dir"]
        dry_run = options["dry_run"]
        include = options["include"]
        exclude = options["exclude"]
        verbosity = options["verbosity"]

        # Validate regex patterns upfront
        if include:
            try:
                re.compile(include)
            except re.error as e:
                raise CommandError(
                    f"Invalid --include pattern: '{include}'. "
                    f"Must be valid regex. Error: {e}"
                ) from e

        if exclude:
            try:
                re.compile(exclude)
            except re.error as e:
                raise CommandError(
                    f"Invalid --exclude pattern: '{exclude}'. "
                    f"Must be valid regex. Error: {e}"
                ) from e

        # Resolve output directory
        if output_dir is None:
            settings = get_apcore_settings()
            output_dir = settings.module_dir

        # Get scanner
        try:
            scanner = get_scanner(source)
        except ImportError as e:
            raise CommandError(str(e)) from e
        except ValueError as e:
            raise CommandError(str(e)) from e

        # Run scan
        source_name = scanner.get_source_name()
        if verbosity >= 1:
            self.stdout.write(f"[django-apcore] Scanning {source_name} endpoints...")

        try:
            modules = scanner.scan(include=include, exclude=exclude)
        except ImportError as e:
            raise CommandError(str(e)) from e
        except re.error as e:
            raise CommandError(
                f"Invalid --include or --exclude pattern. "
                f"Must be valid regex. Error: {e}"
            ) from e

        if verbosity >= 1:
            self.stdout.write(f"[django-apcore] Found {len(modules)} endpoints.")

        if not modules:
            self.stdout.write(
                f"[django-apcore] No endpoints found for source '{source}'. "
                f"Ensure your API is configured."
            )

        # Report warnings
        if modules:
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
                    f"[django-apcore] Generated {len(modules)} " f"module definitions."
                )
                self.stdout.write(
                    f"[django-apcore] Written {len(result)} files " f"to {output_dir}/"
                )

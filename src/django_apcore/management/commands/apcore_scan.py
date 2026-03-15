"""apcore_scan management command.

Orchestrates scanning of Django API endpoints and writing output files.

Usage:
    manage.py apcore_scan --source ninja --output yaml
    manage.py apcore_scan --source drf --output python --dir ./modules/
    manage.py apcore_scan --source ninja --output registry
    manage.py apcore_scan --source ninja --dry-run --include "users.*"
    manage.py apcore_scan --source ninja --ai-enhance
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
            choices=["yaml", "python", "registry"],
            help=(
                "Output format: 'yaml' for .binding.yaml files, "
                "'python' for @module files, "
                "'registry' for direct registry registration. Default: yaml."
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
        parser.add_argument(
            "--verify",
            action="store_true",
            default=False,
            help="Verify written output files (syntax, YAML validity, etc.).",
        )
        parser.add_argument(
            "--ai-enhance",
            action="store_true",
            default=None,
            dest="ai_enhance",
            help=(
                "Enhance module metadata using a local SLM via apcore-toolkit's "
                "AIEnhancer. Requires APCORE_AI_ENABLED=true or explicit flag."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        source = options["source"]
        output_format = options["output"]
        output_dir = options["dir"]
        dry_run = options["dry_run"]
        include = options["include"]
        exclude = options["exclude"]
        verbosity = options["verbosity"]
        verify = options["verify"]
        ai_enhance_flag = options["ai_enhance"]

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
        settings = get_apcore_settings()
        if output_dir is None:
            output_dir = settings.module_dir

        # Resolve AI enhancement
        ai_enhance = (
            ai_enhance_flag if ai_enhance_flag is not None else settings.ai_enhance
        )

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

        # AI enhancement
        if modules and ai_enhance:
            try:
                from apcore_toolkit import AIEnhancer

                enhancer = AIEnhancer()
                if enhancer.is_enabled():
                    if verbosity >= 1:
                        self.stdout.write(
                            "[django-apcore] Enhancing modules with AI..."
                        )
                    modules = enhancer.enhance(modules)
                    if verbosity >= 1:
                        self.stdout.write("[django-apcore] AI enhancement complete.")
                else:
                    self.stdout.write(
                        "[django-apcore] AI enhancement requested but "
                        "APCORE_AI_ENABLED is not set. Skipping."
                    )
            except ImportError:
                self.stdout.write(
                    "[django-apcore] apcore-toolkit AIEnhancer not available. "
                    "Skipping AI enhancement."
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
        if output_format == "registry":
            # Registry writer needs a registry instance
            from django_apcore.output.registry_writer import DjangoRegistryWriter
            from django_apcore.registry import get_registry

            writer = DjangoRegistryWriter()
            registry = get_registry()

            if dry_run:
                if verbosity >= 1:
                    self.stdout.write(
                        "[django-apcore] Dry run -- no modules registered."
                    )
                result = writer.write(modules, registry, dry_run=True)
                if verbosity >= 2:
                    for item in result:
                        self.stdout.write(
                            f"[django-apcore] Would register: {item.module_id}"
                        )
            else:
                result = writer.write(modules, registry, verify=verify)
                if verbosity >= 1:
                    self.stdout.write(
                        f"[django-apcore] Registered {len(result)} modules "
                        f"into registry."
                    )
                # Report verification failures
                if verify:
                    failures = [r for r in result if not r.verified]
                    if failures:
                        for f in failures:
                            self.stderr.write(
                                f"[django-apcore] Verification failed for "
                                f"{f.module_id}: {f.verification_error}"
                            )
        else:
            writer = get_writer(output_format)

            if dry_run:
                if verbosity >= 1:
                    self.stdout.write("[django-apcore] Dry run -- no files written.")
                result = writer.write(modules, output_dir, dry_run=True)
                if verbosity >= 2:
                    for item in result:
                        self.stdout.write(
                            f"[django-apcore] Would write: {item.module_id}"
                        )
            else:
                result = writer.write(modules, output_dir, verify=verify)
                if verbosity >= 1:
                    self.stdout.write(
                        f"[django-apcore] Generated {len(modules)} "
                        f"module definitions."
                    )
                    self.stdout.write(
                        f"[django-apcore] Written {len(result)} files "
                        f"to {output_dir}/"
                    )
                # Report verification failures
                if verify:
                    failures = [r for r in result if not r.verified]
                    if failures:
                        for f in failures:
                            self.stderr.write(
                                f"[django-apcore] Verification failed for "
                                f"{f.module_id}: {f.verification_error}"
                            )

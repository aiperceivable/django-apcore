"""apcore_export management command.

Exports registered apcore modules to external tool formats (e.g., OpenAI Tools).

Usage:
    manage.py apcore_export --format openai-tools
    manage.py apcore_export --format openai-tools --strict
    manage.py apcore_export --format openai-tools --tags users products
    manage.py apcore_export --format openai-tools --prefix myapp
"""

from __future__ import annotations

import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_apcore.registry import get_registry


class Command(BaseCommand):
    help = "Export registered apcore modules to external tool formats."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--format",
            type=str,
            default="openai-tools",
            choices=["openai-tools"],
            help="Export format. Default: 'openai-tools'.",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            default=False,
            help="Enable strict mode for OpenAI Structured Outputs.",
        )
        parser.add_argument(
            "--embed-annotations",
            action="store_true",
            default=False,
            help="Embed module annotations in output.",
        )
        parser.add_argument(
            "--tags",
            nargs="*",
            default=None,
            help="Filter by tags.",
        )
        parser.add_argument(
            "--prefix",
            type=str,
            default=None,
            help="Prefix for tool names.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        registry = get_registry()

        if registry.count == 0:
            raise CommandError(
                "No apcore modules registered. "
                "Run 'manage.py apcore_scan' first or define modules "
                "with @module decorator."
            )

        try:
            from apcore_mcp import to_openai_tools
        except ImportError:
            raise CommandError(
                "apcore-mcp is required for apcore_export. "
                "Install with: pip install django-apcore[mcp]"
            ) from None

        fmt = options["format"]

        if fmt == "openai-tools":
            kwargs: dict[str, Any] = {}
            if options["strict"]:
                kwargs["strict"] = True
            if options["embed_annotations"]:
                kwargs["embed_annotations"] = True
            if options["tags"]:
                kwargs["tags"] = options["tags"]
            if options["prefix"]:
                kwargs["prefix"] = options["prefix"]

            tools = to_openai_tools(registry, **kwargs)
            self.stdout.write(json.dumps(tools, indent=2))

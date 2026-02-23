# tests/test_export_command.py
"""Tests for the apcore_export management command."""

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

_CMD = "django_apcore.management.commands.apcore_export"


def _mock_registry(count=5):
    mock = MagicMock()
    mock.count = count
    return mock


class TestApcoreExportCommand:
    """Test the apcore_export management command."""

    def test_command_exists(self):
        """apcore_export command is discoverable by Django."""
        from django.core.management import get_commands

        commands = get_commands()
        assert "apcore_export" in commands

    def test_empty_registry_raises_error(self):
        """CommandError when no modules are registered."""
        with patch(f"{_CMD}.get_registry") as mock_reg:
            mock_reg.return_value = _mock_registry(count=0)

            with pytest.raises(CommandError, match="No apcore modules registered"):
                call_command("apcore_export")

    def test_missing_apcore_mcp_raises_error(self):
        """CommandError when apcore-mcp is not installed."""
        with (
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(
                f"{_CMD}.to_openai_tools",
                side_effect=ImportError,
                create=True,
            ),
        ):
            mock_reg.return_value = _mock_registry()

            # The import error happens inside handle(), not at the module level
            # We need to mock the import mechanism
            import builtins

            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "apcore_mcp":
                    raise ImportError("No module named 'apcore_mcp'")
                return original_import(name, *args, **kwargs)

            with (
                patch("builtins.__import__", side_effect=mock_import),
                pytest.raises(CommandError, match="apcore-mcp"),
            ):
                call_command("apcore_export")

    def test_json_output(self):
        """Output is valid JSON."""
        with (
            patch(f"{_CMD}.get_registry") as mock_reg,
            patch(f"{_CMD}.json") as mock_json,
        ):
            mock_reg.return_value = _mock_registry()

            mock_tools = [{"type": "function", "function": {"name": "test"}}]

            # We need to mock the lazy import inside handle()
            mock_mod = MagicMock(to_openai_tools=MagicMock(return_value=mock_tools))
            with patch.dict(
                "sys.modules",
                {"apcore_mcp": mock_mod},
            ):
                out = StringIO()
                # Reset json mock to use real json
                mock_json.dumps = json.dumps

                call_command("apcore_export", stdout=out)
                output = out.getvalue()
                parsed = json.loads(output)
                assert isinstance(parsed, list)

    def test_strict_flag_passed(self):
        """--strict flag is forwarded to to_openai_tools()."""
        with patch(f"{_CMD}.get_registry") as mock_reg:
            mock_reg.return_value = _mock_registry()

            mock_to_openai = MagicMock(return_value=[])
            with patch.dict(
                "sys.modules",
                {"apcore_mcp": MagicMock(to_openai_tools=mock_to_openai)},
            ):
                call_command("apcore_export", "--strict")
                call_kwargs = mock_to_openai.call_args
                assert call_kwargs.kwargs.get("strict") is True

    def test_tags_passed(self):
        """--tags are forwarded to to_openai_tools()."""
        with patch(f"{_CMD}.get_registry") as mock_reg:
            mock_reg.return_value = _mock_registry()

            mock_to_openai = MagicMock(return_value=[])
            with patch.dict(
                "sys.modules",
                {"apcore_mcp": MagicMock(to_openai_tools=mock_to_openai)},
            ):
                call_command("apcore_export", "--tags", "users", "products")
                call_kwargs = mock_to_openai.call_args
                assert call_kwargs.kwargs.get("tags") == [
                    "users",
                    "products",
                ]

    def test_prefix_passed(self):
        """--prefix is forwarded to to_openai_tools()."""
        with patch(f"{_CMD}.get_registry") as mock_reg:
            mock_reg.return_value = _mock_registry()

            mock_to_openai = MagicMock(return_value=[])
            with patch.dict(
                "sys.modules",
                {"apcore_mcp": MagicMock(to_openai_tools=mock_to_openai)},
            ):
                call_command("apcore_export", "--prefix", "myapp")
                call_kwargs = mock_to_openai.call_args
                assert call_kwargs.kwargs.get("prefix") == "myapp"

    def test_embed_annotations_passed(self):
        """--embed-annotations is forwarded to to_openai_tools()."""
        with patch(f"{_CMD}.get_registry") as mock_reg:
            mock_reg.return_value = _mock_registry()

            mock_to_openai = MagicMock(return_value=[])
            with patch.dict(
                "sys.modules",
                {"apcore_mcp": MagicMock(to_openai_tools=mock_to_openai)},
            ):
                call_command("apcore_export", "--embed-annotations")
                call_kwargs = mock_to_openai.call_args
                assert call_kwargs.kwargs.get("embed_annotations") is True

    def test_default_format_is_openai_tools(self):
        """Default format is openai-tools."""
        with patch(f"{_CMD}.get_registry") as mock_reg:
            mock_reg.return_value = _mock_registry()

            mock_to_openai = MagicMock(return_value=[])
            with patch.dict(
                "sys.modules",
                {"apcore_mcp": MagicMock(to_openai_tools=mock_to_openai)},
            ):
                call_command("apcore_export")
                mock_to_openai.assert_called_once()

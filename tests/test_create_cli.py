"""Tests for DjangoApcore.create_cli (apcore-cli integration)."""

from __future__ import annotations

from unittest.mock import patch

import click
import pytest
from apcore_toolkit.types import ScannedModule
from click.testing import CliRunner

from django_apcore import DjangoApcore


def _module(module_id: str, method: str, path: str) -> ScannedModule:
    return ScannedModule(
        module_id=module_id,
        description=f"{method} {path}",
        input_schema={"type": "object", "properties": {}},
        output_schema={"type": "object"},
        tags=["orders"],
        target="unused:proxy",
        metadata={"http_method": method, "url_path": path},
    )


@pytest.fixture
def scanned():
    return [
        _module("orders.list_orders", "GET", "/orders"),
        _module("orders.delete_order", "DELETE", "/orders/{order_id}"),
    ]


class TestCreateCli:
    def test_returns_click_group(self, scanned):
        apcore = DjangoApcore()
        with patch.object(DjangoApcore, "scan", return_value=scanned):
            cli = apcore.create_cli(
                prog_name="test-cli", base_url="http://localhost:8000"
            )
        assert isinstance(cli, click.Group)

    def test_help_runs(self, scanned):
        apcore = DjangoApcore()
        with patch.object(DjangoApcore, "scan", return_value=scanned):
            cli = apcore.create_cli(
                prog_name="test-cli", base_url="http://localhost:8000"
            )
        result = CliRunner().invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "test-cli" in result.output

    def test_list_command_shows_scanned_modules(self, scanned):
        apcore = DjangoApcore()
        with patch.object(DjangoApcore, "scan", return_value=scanned):
            cli = apcore.create_cli(
                prog_name="test-cli", base_url="http://localhost:8000"
            )
        result = CliRunner().invoke(cli, ["list"])
        assert result.exit_code == 0
        # both scanned routes should be discoverable
        assert "orders" in result.output

    def test_scan_source_forwarded(self, scanned):
        apcore = DjangoApcore()
        with patch.object(DjangoApcore, "scan", return_value=scanned) as mock_scan:
            apcore.create_cli(prog_name="test-cli", scan_source="drf")
        mock_scan.assert_called_once()
        assert mock_scan.call_args.kwargs.get("source") == "drf"

    def test_missing_apcore_cli_raises_helpful_error(self, scanned):
        apcore = DjangoApcore()
        # Simulate apcore-cli not installed.
        import builtins

        real_import = builtins.__import__

        def _fake_import(name, *args, **kwargs):
            if name.startswith("apcore_cli"):
                raise ImportError("no apcore_cli")
            return real_import(name, *args, **kwargs)

        with (
            patch.object(DjangoApcore, "scan", return_value=scanned),
            patch.object(builtins, "__import__", side_effect=_fake_import),
            pytest.raises(ImportError, match="django-apcore\\[cli\\]"),
        ):
            apcore.create_cli()

# tests/test_scanner_ninja.py
from unittest.mock import patch

import pytest


class TestNinjaScanner:
    """Test NinjaScanner endpoint extraction."""

    def test_get_source_name(self):
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        assert scanner.get_source_name() == "django-ninja"

    def test_scan_returns_list_of_scanned_modules(self):
        """scan() returns a list of ScannedModule instances."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        # Mock the internal discovery to return test data
        with (
            patch.object(scanner, "_check_ninja_installed"),
            patch.object(scanner, "_discover_ninja_apis", return_value=[]),
        ):
            result = scanner.scan()
            assert isinstance(result, list)

    def test_scan_empty_project(self):
        """Scanning a project with no NinjaAPI instances returns empty list."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        with (
            patch.object(scanner, "_check_ninja_installed"),
            patch.object(scanner, "_discover_ninja_apis", return_value=[]),
        ):
            result = scanner.scan()
            assert result == []

    def test_module_id_generation(self):
        """Module ID follows BL-001: {api_prefix}.{path_segments}.{method}."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        # Test the ID generation utility
        module_id = scanner._generate_module_id(
            api_prefix="/api/v1",
            path="/users/{id}",
            method="GET",
        )
        assert module_id == "api.v1.users.get"

    def test_module_id_special_chars_replaced(self):
        """Special characters in paths are replaced with underscores."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        module_id = scanner._generate_module_id(
            api_prefix="/api",
            path="/users/{user_id}/posts",
            method="POST",
        )
        assert module_id == "api.users.posts.post"

    def test_description_from_endpoint_description(self):
        """BL-004: Priority 1 - endpoint description parameter."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        desc = scanner._extract_description(
            description="Custom description",
            docstring="Docstring text",
            operation_id="test_op",
        )
        assert desc == "Custom description"

    def test_description_from_docstring(self):
        """BL-004: Priority 2 - docstring first line."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        desc = scanner._extract_description(
            description=None,
            docstring="First line of docstring.\n\nMore details.",
            operation_id="test_op",
        )
        assert desc == "First line of docstring."

    def test_description_fallback(self):
        """BL-004: Priority 3 - fallback message."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        desc = scanner._extract_description(
            description=None,
            docstring=None,
            operation_id="list_users",
        )
        assert desc == "No description available for list_users"

    def test_include_filter(self):
        """Include filter only keeps matching modules."""
        from django_apcore.scanners.base import ScannedModule
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        modules = [
            ScannedModule(
                module_id="api.users.list",
                description="",
                input_schema={},
                output_schema={},
                tags=[],
                target="a:b",
            ),
            ScannedModule(
                module_id="api.products.list",
                description="",
                input_schema={},
                output_schema={},
                tags=[],
                target="a:b",
            ),
        ]
        with (
            patch.object(scanner, "_check_ninja_installed"),
            patch.object(scanner, "_scan_all_endpoints", return_value=modules),
        ):
            result = scanner.scan(include=r"users")
            assert len(result) == 1
            assert result[0].module_id == "api.users.list"

    def test_exclude_filter(self):
        """Exclude filter removes matching modules."""
        from django_apcore.scanners.base import ScannedModule
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        modules = [
            ScannedModule(
                module_id="api.users.list",
                description="",
                input_schema={},
                output_schema={},
                tags=[],
                target="a:b",
            ),
            ScannedModule(
                module_id="api.users.create",
                description="",
                input_schema={},
                output_schema={},
                tags=[],
                target="a:b",
            ),
        ]
        with (
            patch.object(scanner, "_check_ninja_installed"),
            patch.object(scanner, "_scan_all_endpoints", return_value=modules),
        ):
            result = scanner.scan(exclude=r"create")
            assert len(result) == 1

    def test_duplicate_module_id_resolution(self):
        """BL-003: Duplicate module IDs get numeric suffix."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        ids = scanner._deduplicate_ids(["users.list", "users.list", "users.list"])
        assert ids == ["users.list", "users.list_2", "users.list_3"]


class TestNinjaImportGuard:
    """Test that NinjaScanner handles missing django-ninja gracefully."""

    def test_import_error_message(self):
        """If django-ninja is not installed, a clear error is raised on scan()."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        with (
            patch.object(
                scanner,
                "_check_ninja_installed",
                side_effect=ImportError(
                    "django-ninja is required for --source ninja. "
                    "Install with: pip install django-apcore[ninja]"
                ),
            ),
            pytest.raises(ImportError, match="django-ninja is required"),
        ):
            scanner.scan()

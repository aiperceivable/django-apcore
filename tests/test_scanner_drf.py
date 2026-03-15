# tests/test_scanner_drf.py
from unittest.mock import patch

import pytest


@pytest.fixture
def sample_openapi_schema():
    """A minimal OpenAPI 3.0 schema as would be returned by drf-spectacular."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/api/users/": {
                "get": {
                    "operationId": "users_list",
                    "description": "List all users.",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "results": {"type": "array"},
                                            "count": {"type": "integer"},
                                        },
                                    }
                                }
                            }
                        }
                    },
                },
                "post": {
                    "operationId": "users_create",
                    "description": "Create a user.",
                    "tags": ["users"],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"},
                                    },
                                    "required": ["name", "email"],
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                        },
                                    }
                                }
                            }
                        }
                    },
                },
            },
        },
    }


def _mock_scan(scanner, schema):
    """Context manager that mocks both _check_drf_installed and _get_openapi_schema.

    drf-spectacular is not installed in the test environment, so we must
    bypass the import check when testing scan() logic.
    """
    return (
        patch.object(scanner, "_check_drf_installed"),
        patch.object(scanner, "_get_openapi_schema", return_value=schema),
    )


class TestDRFScanner:
    """Test DRFScanner OpenAPI schema extraction."""

    def test_get_source_name(self):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        assert scanner.get_source_name() == "drf-spectacular"

    def test_scan_returns_list(self):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        mock_check, mock_schema = _mock_scan(scanner, {"paths": {}})
        with mock_check, mock_schema:
            result = scanner.scan()
            assert isinstance(result, list)

    def test_scan_extracts_endpoints(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        mock_check, mock_schema = _mock_scan(scanner, sample_openapi_schema)
        with mock_check, mock_schema:
            result = scanner.scan()
            assert len(result) == 2

    def test_module_id_generation(self):
        """Module ID follows BL-002: {app_label}.{viewset_name}.{action}."""
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        module_id = scanner._generate_module_id(
            path="/api/users/",
            method="get",
            operation_id="users_list",
        )
        assert module_id == "users.list"

    def test_module_id_from_path_when_no_operation_id(self):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        module_id = scanner._generate_module_id(
            path="/api/v2/products/",
            method="post",
            operation_id=None,
        )
        assert "products" in module_id
        assert "post" in module_id

    def test_description_from_operation(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        mock_check, mock_schema = _mock_scan(scanner, sample_openapi_schema)
        with mock_check, mock_schema:
            result = scanner.scan()
            assert result[0].description == "List all users."

    def test_description_fallback(self):
        """BL-005: Fallback when no description available."""
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        desc = scanner._extract_description(
            description=None,
            summary=None,
            operation_id="users_list",
        )
        assert desc == "No description available for users_list"

    def test_input_schema_from_request_body(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        mock_check, mock_schema = _mock_scan(scanner, sample_openapi_schema)
        with mock_check, mock_schema:
            result = scanner.scan()
            create_module = [m for m in result if "create" in m.module_id][0]
            assert "name" in create_module.input_schema.get("properties", {})
            assert "email" in create_module.input_schema.get("properties", {})

    def test_input_schema_from_query_params(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        mock_check, mock_schema = _mock_scan(scanner, sample_openapi_schema)
        with mock_check, mock_schema:
            result = scanner.scan()
            list_module = [m for m in result if "list" in m.module_id][0]
            assert "page" in list_module.input_schema.get("properties", {})

    def test_output_schema_from_response(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        mock_check, mock_schema = _mock_scan(scanner, sample_openapi_schema)
        with mock_check, mock_schema:
            result = scanner.scan()
            list_module = [m for m in result if "list" in m.module_id][0]
            assert "properties" in list_module.output_schema

    def test_tags_from_operation(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        mock_check, mock_schema = _mock_scan(scanner, sample_openapi_schema)
        with mock_check, mock_schema:
            result = scanner.scan()
            assert result[0].tags == ["users"]

    def test_include_filter(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        mock_check, mock_schema = _mock_scan(scanner, sample_openapi_schema)
        with mock_check, mock_schema:
            result = scanner.scan(include=r"list")
            assert len(result) == 1

    def test_exclude_filter(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        mock_check, mock_schema = _mock_scan(scanner, sample_openapi_schema)
        with mock_check, mock_schema:
            result = scanner.scan(exclude=r"create")
            assert len(result) == 1

    def test_duplicate_ids_resolved(self):
        """BL-003: Duplicate IDs get numeric suffix."""
        from django_apcore.scanners.base import ScannedModule
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        modules = [
            ScannedModule(
                module_id="users.list",
                description="",
                input_schema={},
                output_schema={},
                tags=[],
                target="a:b",
            ),
            ScannedModule(
                module_id="users.list",
                description="",
                input_schema={},
                output_schema={},
                tags=[],
                target="a:b",
            ),
        ]
        result = scanner.deduplicate_ids(modules)
        ids = [m.module_id for m in result]
        assert ids == ["users.list", "users.list_2"]

    def test_target_format_has_colon(self, sample_openapi_schema):
        """Target must be in 'module.path:callable' format for PythonWriter."""
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        mock_check, mock_schema = _mock_scan(scanner, sample_openapi_schema)
        with mock_check, mock_schema:
            result = scanner.scan()
            for module in result:
                assert (
                    ":" in module.target
                ), f"Target {module.target!r} missing colon separator"
                parts = module.target.split(":")
                assert len(parts) == 2
                assert parts[0]  # module path is non-empty
                assert parts[1]  # callable name is non-empty

    def test_empty_schema_returns_empty(self):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        mock_check, mock_schema = _mock_scan(scanner, {"paths": {}})
        with mock_check, mock_schema:
            result = scanner.scan()
            assert result == []


class TestDRFImportGuard:
    """Test that DRFScanner handles missing drf-spectacular gracefully."""

    def test_import_error_message(self):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        with (
            patch.object(
                scanner,
                "_check_drf_installed",
                side_effect=ImportError(
                    "drf-spectacular is required for --source drf. "
                    "Install with: pip install django-apcore[drf]"
                ),
            ),
            pytest.raises(ImportError, match="drf-spectacular is required"),
        ):
            scanner.scan()

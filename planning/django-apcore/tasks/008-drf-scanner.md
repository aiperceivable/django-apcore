# Task 008: DRFScanner Implementation

## Goal

Implement `DRFScanner`, a `BaseScanner` subclass that uses `drf-spectacular`'s `SchemaGenerator.get_schema()` to produce an OpenAPI 3.0 document, iterates over operations, extracts request/response schemas, and produces `ScannedModule` instances. Requires `drf-spectacular >= 0.27` as an optional dependency.

## Files Involved

### Create

- `src/django_apcore/scanners/drf.py` -- `DRFScanner` class

### Modify

- `src/django_apcore/scanners/__init__.py` -- Already has `get_scanner()` dispatching to DRFScanner

### Test

- `tests/test_scanner_drf.py` -- Unit tests with mocked OpenAPI schema
- `tests/fixtures/drf_project/` -- Minimal DRF fixture project (optional, for integration)

## Steps

### Step 1: Write tests (TDD -- Red phase)

Create `tests/test_scanner_drf.py`:

```python
# tests/test_scanner_drf.py
import pytest
from unittest.mock import MagicMock, patch


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


class TestDRFScanner:
    """Test DRFScanner OpenAPI schema extraction."""

    def test_get_source_name(self):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        assert scanner.get_source_name() == "drf-spectacular"

    def test_scan_returns_list(self):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        with patch.object(scanner, "_get_openapi_schema", return_value={"paths": {}}):
            result = scanner.scan()
            assert isinstance(result, list)

    def test_scan_extracts_endpoints(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        with patch.object(scanner, "_get_openapi_schema", return_value=sample_openapi_schema):
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
        with patch.object(scanner, "_get_openapi_schema", return_value=sample_openapi_schema):
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
        with patch.object(scanner, "_get_openapi_schema", return_value=sample_openapi_schema):
            result = scanner.scan()
            create_module = [m for m in result if "create" in m.module_id][0]
            assert "name" in create_module.input_schema.get("properties", {})
            assert "email" in create_module.input_schema.get("properties", {})

    def test_input_schema_from_query_params(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        with patch.object(scanner, "_get_openapi_schema", return_value=sample_openapi_schema):
            result = scanner.scan()
            list_module = [m for m in result if "list" in m.module_id][0]
            assert "page" in list_module.input_schema.get("properties", {})

    def test_output_schema_from_response(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        with patch.object(scanner, "_get_openapi_schema", return_value=sample_openapi_schema):
            result = scanner.scan()
            list_module = [m for m in result if "list" in m.module_id][0]
            assert "properties" in list_module.output_schema

    def test_tags_from_operation(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        with patch.object(scanner, "_get_openapi_schema", return_value=sample_openapi_schema):
            result = scanner.scan()
            assert result[0].tags == ["users"]

    def test_include_filter(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        with patch.object(scanner, "_get_openapi_schema", return_value=sample_openapi_schema):
            result = scanner.scan(include=r"list")
            assert len(result) == 1

    def test_exclude_filter(self, sample_openapi_schema):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        with patch.object(scanner, "_get_openapi_schema", return_value=sample_openapi_schema):
            result = scanner.scan(exclude=r"create")
            assert len(result) == 1

    def test_duplicate_ids_resolved(self):
        """BL-003: Duplicate IDs get numeric suffix."""
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        ids = scanner._deduplicate_ids(["users.list", "users.list"])
        assert ids == ["users.list", "users.list_2"]

    def test_empty_schema_returns_empty(self):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        with patch.object(scanner, "_get_openapi_schema", return_value={"paths": {}}):
            result = scanner.scan()
            assert result == []


class TestDRFImportGuard:
    """Test that DRFScanner handles missing drf-spectacular gracefully."""

    def test_import_error_message(self):
        from django_apcore.scanners.drf import DRFScanner

        scanner = DRFScanner()
        with patch.object(scanner, "_check_drf_installed", side_effect=ImportError(
            "drf-spectacular is required for --source drf. "
            "Install with: pip install django-apcore[drf]"
        )):
            with pytest.raises(ImportError, match="drf-spectacular is required"):
                scanner.scan()
```

### Step 2: Run tests -- verify they fail

```bash
pytest tests/test_scanner_drf.py -x --tb=short
```

Expected: `ImportError: No module named 'django_apcore.scanners.drf'`

### Step 3: Implement

Create `src/django_apcore/scanners/drf.py`:

```python
"""DRFScanner: scans DRF ViewSets via drf-spectacular OpenAPI generation.

Requires drf-spectacular >= 0.27 (optional dependency).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from django_apcore.scanners.base import BaseScanner, ScannedModule

logger = logging.getLogger("django_apcore")


class DRFScanner(BaseScanner):
    """Scanner for Django REST Framework endpoints.

    Uses drf-spectacular's SchemaGenerator to produce an OpenAPI 3.0 document,
    then iterates over operations to extract schemas.
    """

    def get_source_name(self) -> str:
        return "drf-spectacular"

    def scan(
        self,
        include: str | None = None,
        exclude: str | None = None,
    ) -> list[ScannedModule]:
        """Scan all DRF endpoints via drf-spectacular.

        Args:
            include: Regex pattern to include (matches against module_id).
            exclude: Regex pattern to exclude.

        Returns:
            List of ScannedModule instances.

        Raises:
            ImportError: If drf-spectacular is not installed.
        """
        self._check_drf_installed()
        schema = self._get_openapi_schema()
        modules = self._schema_to_modules(schema)
        return self.filter_modules(modules, include, exclude)

    def _check_drf_installed(self) -> None:
        """Verify drf-spectacular is available."""
        try:
            import drf_spectacular  # noqa: F401
        except ImportError:
            raise ImportError(
                "drf-spectacular is required for --source drf. "
                "Install with: pip install django-apcore[drf]"
            )

    def _get_openapi_schema(self) -> dict[str, Any]:
        """Generate OpenAPI 3.0 schema via drf-spectacular."""
        from drf_spectacular.generators import SchemaGenerator

        generator = SchemaGenerator()
        schema = generator.get_schema()
        return schema

    def _schema_to_modules(self, schema: dict[str, Any]) -> list[ScannedModule]:
        """Convert OpenAPI schema to list of ScannedModules."""
        modules = []
        paths = schema.get("paths", {})

        for path, methods in paths.items():
            for method, operation in methods.items():
                if not isinstance(operation, dict):
                    continue
                if method.lower() not in ("get", "post", "put", "patch", "delete"):
                    continue

                module = self._operation_to_module(path, method, operation)
                if module:
                    modules.append(module)

        # Deduplicate IDs
        if modules:
            deduped_ids = self._deduplicate_ids([m.module_id for m in modules])
            for i, module in enumerate(modules):
                if module.module_id != deduped_ids[i]:
                    modules[i] = ScannedModule(
                        module_id=deduped_ids[i],
                        description=module.description,
                        input_schema=module.input_schema,
                        output_schema=module.output_schema,
                        tags=module.tags,
                        target=module.target,
                        version=module.version,
                        warnings=module.warnings + [
                            f"Module ID renamed from '{module.module_id}' to '{deduped_ids[i]}' to avoid collision"
                        ],
                    )

        return modules

    def _operation_to_module(
        self, path: str, method: str, operation: dict[str, Any]
    ) -> ScannedModule | None:
        """Convert a single OpenAPI operation to a ScannedModule."""
        try:
            operation_id = operation.get("operationId")
            module_id = self._generate_module_id(path, method, operation_id)

            description = self._extract_description(
                description=operation.get("description"),
                summary=operation.get("summary"),
                operation_id=operation_id or module_id,
            )

            input_schema = self._extract_input_schema(operation)
            output_schema = self._extract_output_schema(operation)
            tags = operation.get("tags", [])

            # Target is the operation_id or a path-based fallback
            target = operation_id or module_id

            warnings: list[str] = []
            if not operation.get("description") and not operation.get("summary"):
                warnings.append(
                    f"Endpoint '{method.upper()} {path}' has no description"
                )

            return ScannedModule(
                module_id=module_id,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                tags=tags,
                target=target,
                warnings=warnings,
            )
        except Exception:
            logger.warning(
                "Failed to scan endpoint %s %s", method.upper(), path, exc_info=True
            )
            return None

    def _generate_module_id(
        self, path: str, method: str, operation_id: str | None
    ) -> str:
        """Generate module ID per BL-002.

        If operation_id is available (from drf-spectacular), derive from it.
        Otherwise, use path + method.
        """
        if operation_id:
            # drf-spectacular generates IDs like "users_list", "users_create"
            # Convert to dotted format: "users.list"
            module_id = operation_id.replace("_", ".")
            return module_id.lower()

        # Fallback: use path segments
        cleaned = path.strip("/")
        # Remove common API prefixes
        cleaned = re.sub(r"^api/v?\d*/", "", cleaned)
        # Remove path parameters
        cleaned = re.sub(r"\{[^}]+\}", "", cleaned)
        # Convert to dots
        cleaned = re.sub(r"[^a-zA-Z0-9]+", ".", cleaned).strip(".")
        return f"{cleaned}.{method}".lower()

    def _extract_description(
        self,
        description: str | None,
        summary: str | None,
        operation_id: str,
    ) -> str:
        """Extract description per BL-005 priority chain."""
        if description:
            return description
        if summary:
            return summary
        return f"No description available for {operation_id}"

    def _extract_input_schema(self, operation: dict[str, Any]) -> dict[str, Any]:
        """Extract input schema from OpenAPI operation."""
        schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

        # Query/path parameters
        for param in operation.get("parameters", []):
            if param.get("in") in ("query", "path"):
                name = param["name"]
                param_schema = param.get("schema", {"type": "string"})
                schema["properties"][name] = param_schema
                if param.get("required", False):
                    schema["required"].append(name)

        # Request body
        request_body = operation.get("requestBody", {})
        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        body_schema = json_content.get("schema", {})
        if body_schema:
            schema["properties"].update(body_schema.get("properties", {}))
            schema["required"].extend(body_schema.get("required", []))

        return schema

    def _extract_output_schema(self, operation: dict[str, Any]) -> dict[str, Any]:
        """Extract output schema from responses (200/201)."""
        responses = operation.get("responses", {})
        for status_code in ("200", "201"):
            response = responses.get(status_code, {})
            content = response.get("content", {})
            json_content = content.get("application/json", {})
            if "schema" in json_content:
                return json_content["schema"]

        return {"type": "object", "properties": {}}

    def _deduplicate_ids(self, ids: list[str]) -> list[str]:
        """Resolve duplicate module IDs per BL-003."""
        seen: dict[str, int] = {}
        result = []
        for id_ in ids:
            if id_ in seen:
                seen[id_] += 1
                result.append(f"{id_}_{seen[id_]}")
            else:
                seen[id_] = 1
                result.append(id_)
        return result
```

### Step 4: Run tests -- verify they pass

```bash
pytest tests/test_scanner_drf.py -x --tb=short -v
```

All tests should pass.

### Step 5: Commit

```bash
git add src/django_apcore/scanners/drf.py tests/test_scanner_drf.py
git commit -m "feat: DRFScanner for DRF ViewSet scanning via drf-spectacular"
```

## Acceptance Criteria

- [ ] `DRFScanner` extends `BaseScanner` and implements `scan()` and `get_source_name()`
- [ ] `get_source_name()` returns `"drf-spectacular"`
- [ ] Uses `drf_spectacular.generators.SchemaGenerator.get_schema()` to get OpenAPI document
- [ ] Module ID follows BL-002 derivation from `operationId` or path+method fallback
- [ ] Description follows BL-005 priority: operation description > summary > fallback
- [ ] Input schema extracts query params, path params, and request body
- [ ] Output schema uses 200/201 response schema
- [ ] Duplicate module IDs get numeric suffix per BL-003
- [ ] Missing `drf-spectacular` raises `ImportError` with install instructions
- [ ] Handles `SerializerMethodField` by skipping with warning (BL-011)
- [ ] Include/exclude filtering works (inherited from `BaseScanner`)
- [ ] 90% test coverage for `scanners/drf.py`

## Dependencies

- **005-scanner-base** -- Requires `BaseScanner` and `ScannedModule`

## Estimated Time

4 hours

## Troubleshooting

**Issue: `drf-spectacular` is not installed in test environment**
Tests use `unittest.mock.patch` to mock `_get_openapi_schema()`, so `drf-spectacular` is not required for unit tests. Integration tests in `tests/integration/` will require it.

**Issue: `SchemaGenerator.get_schema()` returns different structure in newer drf-spectacular versions**
The OpenAPI 3.0 structure is stable, but drf-spectacular may add extra metadata. The scanner extracts from standard OpenAPI paths, so minor structural differences should not cause issues. Pin to `>=0.27` for consistency.

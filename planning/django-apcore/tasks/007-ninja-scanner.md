# Task 007: NinjaScanner Implementation

## Goal

Implement `NinjaScanner`, a `BaseScanner` subclass that discovers all `NinjaAPI` instances in the Django URL configuration, iterates over their endpoints, extracts Pydantic input/output schemas via `model_json_schema()`, and produces `ScannedModule` instances. Requires `django-ninja >= 1.0` as an optional dependency.

## Files Involved

### Create

- `src/django_apcore/scanners/ninja.py` -- `NinjaScanner` class

### Modify

- `src/django_apcore/scanners/__init__.py` -- Already has `get_scanner()` dispatching to NinjaScanner

### Test

- `tests/test_scanner_ninja.py` -- Unit tests with mocked NinjaAPI instances
- `tests/fixtures/ninja_project/` -- Minimal django-ninja fixture project (optional, for integration)

## Steps

### Step 1: Write tests (TDD -- Red phase)

Create `tests/test_scanner_ninja.py`:

```python
# tests/test_scanner_ninja.py
import pytest
from unittest.mock import MagicMock, patch


class TestNinjaScanner:
    """Test NinjaScanner endpoint extraction."""

    def test_get_source_name(self):
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        assert scanner.get_source_name() == "django-ninja"

    def test_scan_returns_list_of_scanned_modules(self):
        """scan() returns a list of ScannedModule instances."""
        from django_apcore.scanners.ninja import NinjaScanner
        from django_apcore.scanners.base import ScannedModule

        scanner = NinjaScanner()
        # Mock the internal discovery to return test data
        with patch.object(scanner, "_discover_ninja_apis", return_value=[]):
            result = scanner.scan()
            assert isinstance(result, list)

    def test_scan_empty_project(self):
        """Scanning a project with no NinjaAPI instances returns empty list."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        with patch.object(scanner, "_discover_ninja_apis", return_value=[]):
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
        from django_apcore.scanners.ninja import NinjaScanner
        from django_apcore.scanners.base import ScannedModule

        scanner = NinjaScanner()
        modules = [
            ScannedModule(
                module_id="api.users.list", description="", input_schema={},
                output_schema={}, tags=[], target="a:b",
            ),
            ScannedModule(
                module_id="api.products.list", description="", input_schema={},
                output_schema={}, tags=[], target="a:b",
            ),
        ]
        with patch.object(scanner, "_scan_all_endpoints", return_value=modules):
            result = scanner.scan(include=r"users")
            assert len(result) == 1
            assert result[0].module_id == "api.users.list"

    def test_exclude_filter(self):
        """Exclude filter removes matching modules."""
        from django_apcore.scanners.ninja import NinjaScanner
        from django_apcore.scanners.base import ScannedModule

        scanner = NinjaScanner()
        modules = [
            ScannedModule(
                module_id="api.users.list", description="", input_schema={},
                output_schema={}, tags=[], target="a:b",
            ),
            ScannedModule(
                module_id="api.users.create", description="", input_schema={},
                output_schema={}, tags=[], target="a:b",
            ),
        ]
        with patch.object(scanner, "_scan_all_endpoints", return_value=modules):
            result = scanner.scan(exclude=r"create")
            assert len(result) == 1

    def test_duplicate_module_id_resolution(self):
        """BL-003: Duplicate module IDs get numeric suffix."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        ids = scanner._deduplicate_ids([
            "users.list", "users.list", "users.list"
        ])
        assert ids == ["users.list", "users.list_2", "users.list_3"]


class TestNinjaImportGuard:
    """Test that NinjaScanner handles missing django-ninja gracefully."""

    def test_import_error_message(self):
        """If django-ninja is not installed, a clear error is raised on scan()."""
        from django_apcore.scanners.ninja import NinjaScanner

        scanner = NinjaScanner()
        with patch.object(scanner, "_check_ninja_installed", side_effect=ImportError(
            "django-ninja is required for --source ninja. "
            "Install with: pip install django-apcore[ninja]"
        )):
            with pytest.raises(ImportError, match="django-ninja is required"):
                scanner.scan()
```

### Step 2: Run tests -- verify they fail

```bash
pytest tests/test_scanner_ninja.py -x --tb=short
```

Expected: `ImportError: No module named 'django_apcore.scanners.ninja'`

### Step 3: Implement

Create `src/django_apcore/scanners/ninja.py`:

```python
"""NinjaScanner: scans django-ninja API instances for endpoint metadata.

Requires django-ninja >= 1.0 (optional dependency).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from django_apcore.scanners.base import BaseScanner, ScannedModule

logger = logging.getLogger("django_apcore")


class NinjaScanner(BaseScanner):
    """Scanner for django-ninja API endpoints.

    Discovers NinjaAPI instances from Django URL patterns, extracts
    Pydantic input/output schemas, and produces ScannedModule instances.
    """

    def get_source_name(self) -> str:
        return "django-ninja"

    def scan(
        self,
        include: str | None = None,
        exclude: str | None = None,
    ) -> list[ScannedModule]:
        """Scan all django-ninja endpoints.

        Args:
            include: Regex pattern to include (matches against module_id).
            exclude: Regex pattern to exclude.

        Returns:
            List of ScannedModule instances.

        Raises:
            ImportError: If django-ninja is not installed.
        """
        self._check_ninja_installed()
        modules = self._scan_all_endpoints()
        return self.filter_modules(modules, include, exclude)

    def _check_ninja_installed(self) -> None:
        """Verify django-ninja is available."""
        try:
            import ninja  # noqa: F401
        except ImportError:
            raise ImportError(
                "django-ninja is required for --source ninja. "
                "Install with: pip install django-apcore[ninja]"
            )

    def _discover_ninja_apis(self) -> list[Any]:
        """Discover all NinjaAPI instances from Django URL patterns."""
        from django.urls import get_resolver

        apis = []
        try:
            from ninja import NinjaAPI

            resolver = get_resolver()
            self._find_apis(resolver.url_patterns, apis, NinjaAPI)
        except ImportError:
            pass
        return apis

    def _find_apis(self, patterns, apis, api_class) -> None:
        """Recursively search URL patterns for NinjaAPI instances."""
        for pattern in patterns:
            if hasattr(pattern, "callback") and isinstance(
                getattr(pattern.callback, "api", None), api_class
            ):
                api = pattern.callback.api
                if api not in apis:
                    apis.append(api)
            if hasattr(pattern, "url_patterns"):
                self._find_apis(pattern.url_patterns, apis, api_class)

    def _scan_all_endpoints(self) -> list[ScannedModule]:
        """Scan all discovered NinjaAPI instances."""
        apis = self._discover_ninja_apis()
        modules = []
        seen_ids: list[str] = []

        for api in apis:
            api_prefix = getattr(api, "urls_namespace", "") or ""
            try:
                schema = api.get_openapi_schema()
                paths = schema.get("paths", {})

                for path, methods in paths.items():
                    for method, operation in methods.items():
                        if method.lower() in ("get", "post", "put", "patch", "delete"):
                            module = self._operation_to_module(
                                api, api_prefix, path, method, operation
                            )
                            if module:
                                seen_ids.append(module.module_id)
                                modules.append(module)
            except Exception:
                logger.warning("Error scanning NinjaAPI instance", exc_info=True)

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
        self, api, api_prefix: str, path: str, method: str, operation: dict
    ) -> ScannedModule | None:
        """Convert an OpenAPI operation to a ScannedModule."""
        try:
            module_id = self._generate_module_id(api_prefix, path, method)
            operation_id = operation.get("operationId", module_id)

            description = self._extract_description(
                description=operation.get("description"),
                docstring=operation.get("summary"),
                operation_id=operation_id,
            )

            input_schema = self._extract_input_schema(operation)
            output_schema = self._extract_output_schema(operation)

            tags = operation.get("tags", [])
            target = f"{api.__module__}:{operation_id}"

            warnings = []
            if not operation.get("description") and not operation.get("summary"):
                warnings.append(f"Endpoint '{method.upper()} {path}' has no description")

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

    def _generate_module_id(self, api_prefix: str, path: str, method: str) -> str:
        """Generate module ID per BL-001.

        Format: {api_prefix}.{path_segments}.{method} lowercased,
        special chars replaced.
        """
        # Clean prefix and path
        combined = f"{api_prefix}/{path}".strip("/")
        # Remove path parameters (e.g., {id})
        combined = re.sub(r"\{[^}]+\}", "", combined)
        # Replace non-alphanumeric with dots
        combined = re.sub(r"[^a-zA-Z0-9]+", ".", combined)
        # Remove trailing/leading dots
        combined = combined.strip(".")
        # Append method
        module_id = f"{combined}.{method}".lower()
        # Clean up double dots
        module_id = re.sub(r"\.+", ".", module_id)
        return module_id

    def _extract_description(
        self,
        description: str | None,
        docstring: str | None,
        operation_id: str,
    ) -> str:
        """Extract description per BL-004 priority chain."""
        if description:
            return description
        if docstring:
            return docstring.split("\n")[0].strip()
        return f"No description available for {operation_id}"

    def _extract_input_schema(self, operation: dict) -> dict[str, Any]:
        """Extract input schema from OpenAPI operation."""
        schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

        # Query parameters
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

    def _extract_output_schema(self, operation: dict) -> dict[str, Any]:
        """Extract output schema from OpenAPI operation responses."""
        responses = operation.get("responses", {})
        for status_code in ("200", "201"):
            response = responses.get(status_code, {})
            content = response.get("content", {})
            json_content = content.get("application/json", {})
            if "schema" in json_content:
                return json_content["schema"]

        return {"type": "object", "properties": {}}

    def _deduplicate_ids(self, ids: list[str]) -> list[str]:
        """Resolve duplicate module IDs per BL-003.

        Appends _2, _3, etc. to duplicates.
        """
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
pytest tests/test_scanner_ninja.py -x --tb=short -v
```

All tests should pass.

### Step 5: Commit

```bash
git add src/django_apcore/scanners/ninja.py tests/test_scanner_ninja.py
git commit -m "feat: NinjaScanner for django-ninja endpoint scanning"
```

## Acceptance Criteria

- [ ] `NinjaScanner` extends `BaseScanner` and implements `scan()` and `get_source_name()`
- [ ] `get_source_name()` returns `"django-ninja"`
- [ ] Module ID follows BL-001: `{api_prefix}.{path_segments}.{method}` lowercased
- [ ] Path parameters (`{id}`) are stripped from module IDs
- [ ] Description follows BL-004 priority: endpoint description > docstring > fallback
- [ ] Input schema extracts query params, path params, and request body
- [ ] Output schema uses 200/201 response schema
- [ ] Duplicate module IDs get numeric suffix per BL-003 (`_2`, `_3`)
- [ ] Missing `django-ninja` raises `ImportError` with install instructions
- [ ] Include/exclude filtering works (inherited from `BaseScanner`)
- [ ] 90% test coverage for `scanners/ninja.py`

## Dependencies

- **005-scanner-base** -- Requires `BaseScanner` and `ScannedModule`

## Estimated Time

4 hours

## Troubleshooting

**Issue: `django-ninja` is not installed in the test environment**
Tests use `unittest.mock.patch` to mock the NinjaAPI discovery, so `django-ninja` is not required for unit tests. Integration tests in `tests/integration/` will require it.

**Issue: NinjaAPI URL pattern discovery fails**
Different versions of `django-ninja` may organize URL patterns differently. The `_find_apis()` method recursively searches patterns. If it fails, inspect `get_resolver().url_patterns` to understand the structure and adapt the search.

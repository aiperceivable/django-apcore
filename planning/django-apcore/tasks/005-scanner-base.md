# Task 005: BaseScanner ABC + ScannedModule Dataclass

## Goal

Implement `BaseScanner`, an abstract base class defining the scanner interface, and `ScannedModule`, a dataclass representing a single scanned endpoint. These form the foundation for NinjaScanner and DRFScanner. Also implement include/exclude regex filtering as a shared utility in the base class.

## Files Involved

### Create

- `src/django_apcore/scanners/__init__.py` -- Scanner subpackage with `get_scanner()` helper
- `src/django_apcore/scanners/base.py` -- `BaseScanner` ABC and `ScannedModule` dataclass

### Test

- `tests/test_scanner_base.py` -- Unit tests for ABC enforcement, dataclass fields, filtering

## Steps

### Step 1: Write tests (TDD -- Red phase)

Create `tests/test_scanner_base.py`:

```python
# tests/test_scanner_base.py
import re
from dataclasses import fields

import pytest


class TestScannedModule:
    """Test the ScannedModule dataclass."""

    def test_required_fields_exist(self):
        """ScannedModule has all required fields from tech-design."""
        from django_apcore.scanners.base import ScannedModule

        field_names = {f.name for f in fields(ScannedModule)}
        expected = {
            "module_id",
            "description",
            "input_schema",
            "output_schema",
            "tags",
            "target",
            "version",
            "warnings",
        }
        assert expected == field_names

    def test_create_with_required_fields(self):
        """ScannedModule can be created with required fields."""
        from django_apcore.scanners.base import ScannedModule

        module = ScannedModule(
            module_id="api.v1.users.list",
            description="List all users",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object", "properties": {}},
            tags=["users"],
            target="myapp.api:list_users",
        )
        assert module.module_id == "api.v1.users.list"
        assert module.description == "List all users"
        assert module.tags == ["users"]
        assert module.target == "myapp.api:list_users"

    def test_default_version(self):
        """ScannedModule defaults version to '1.0.0'."""
        from django_apcore.scanners.base import ScannedModule

        module = ScannedModule(
            module_id="test",
            description="test",
            input_schema={},
            output_schema={},
            tags=[],
            target="mod:func",
        )
        assert module.version == "1.0.0"

    def test_default_warnings_empty_list(self):
        """ScannedModule defaults warnings to empty list."""
        from django_apcore.scanners.base import ScannedModule

        module = ScannedModule(
            module_id="test",
            description="test",
            input_schema={},
            output_schema={},
            tags=[],
            target="mod:func",
        )
        assert module.warnings == []

    def test_warnings_are_independent_instances(self):
        """Each ScannedModule gets its own warnings list (no shared mutable default)."""
        from django_apcore.scanners.base import ScannedModule

        m1 = ScannedModule(
            module_id="m1", description="", input_schema={},
            output_schema={}, tags=[], target="a:b",
        )
        m2 = ScannedModule(
            module_id="m2", description="", input_schema={},
            output_schema={}, tags=[], target="a:b",
        )
        m1.warnings.append("warning1")
        assert m2.warnings == []


class TestBaseScannerABC:
    """Test that BaseScanner enforces the abstract interface."""

    def test_cannot_instantiate_directly(self):
        """BaseScanner cannot be instantiated without implementing abstract methods."""
        from django_apcore.scanners.base import BaseScanner

        with pytest.raises(TypeError, match="abstract method"):
            BaseScanner()  # type: ignore[abstract]

    def test_subclass_must_implement_scan(self):
        """Subclass without scan() cannot be instantiated."""
        from django_apcore.scanners.base import BaseScanner

        class IncompleteScanner(BaseScanner):
            def get_source_name(self) -> str:
                return "incomplete"

        with pytest.raises(TypeError, match="abstract method"):
            IncompleteScanner()  # type: ignore[abstract]

    def test_subclass_must_implement_get_source_name(self):
        """Subclass without get_source_name() cannot be instantiated."""
        from django_apcore.scanners.base import BaseScanner

        class IncompleteScanner(BaseScanner):
            def scan(self, include=None, exclude=None):
                return []

        with pytest.raises(TypeError, match="abstract method"):
            IncompleteScanner()  # type: ignore[abstract]

    def test_complete_subclass_can_be_instantiated(self):
        """Subclass implementing all abstract methods works."""
        from django_apcore.scanners.base import BaseScanner

        class ConcreteScanner(BaseScanner):
            def scan(self, include=None, exclude=None):
                return []

            def get_source_name(self) -> str:
                return "concrete"

        scanner = ConcreteScanner()
        assert scanner.get_source_name() == "concrete"
        assert scanner.scan() == []


class TestFilterModules:
    """Test the include/exclude filtering utility."""

    def _make_scanner(self):
        from django_apcore.scanners.base import BaseScanner, ScannedModule

        class TestScanner(BaseScanner):
            def scan(self, include=None, exclude=None):
                modules = [
                    ScannedModule(
                        module_id="api.v1.users.list",
                        description="List users",
                        input_schema={}, output_schema={},
                        tags=["users"], target="app:func",
                    ),
                    ScannedModule(
                        module_id="api.v1.users.create",
                        description="Create user",
                        input_schema={}, output_schema={},
                        tags=["users"], target="app:func",
                    ),
                    ScannedModule(
                        module_id="api.v1.products.list",
                        description="List products",
                        input_schema={}, output_schema={},
                        tags=["products"], target="app:func",
                    ),
                ]
                return self.filter_modules(modules, include, exclude)

            def get_source_name(self) -> str:
                return "test"

        return TestScanner()

    def test_no_filters_returns_all(self):
        scanner = self._make_scanner()
        result = scanner.scan()
        assert len(result) == 3

    def test_include_filter(self):
        scanner = self._make_scanner()
        result = scanner.scan(include=r"users")
        assert len(result) == 2
        assert all("users" in m.module_id for m in result)

    def test_exclude_filter(self):
        scanner = self._make_scanner()
        result = scanner.scan(exclude=r"products")
        assert len(result) == 2
        assert all("products" not in m.module_id for m in result)

    def test_include_and_exclude_combined(self):
        scanner = self._make_scanner()
        result = scanner.scan(include=r"api\.v1", exclude=r"create")
        assert len(result) == 2
        assert all("create" not in m.module_id for m in result)

    def test_include_no_match_returns_empty(self):
        scanner = self._make_scanner()
        result = scanner.scan(include=r"nonexistent")
        assert len(result) == 0
```

### Step 2: Run tests -- verify they fail

```bash
pytest tests/test_scanner_base.py -x --tb=short
```

Expected: `ImportError: cannot import name 'ScannedModule' from 'django_apcore.scanners.base'`

### Step 3: Implement

Create `src/django_apcore/scanners/base.py`:

```python
"""Base scanner interface and ScannedModule dataclass.

All scanners (NinjaScanner, DRFScanner) extend BaseScanner and produce
lists of ScannedModule instances.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScannedModule:
    """Result of scanning a single endpoint.

    Attributes:
        module_id: Unique module identifier (e.g., 'api.v1.users.list').
        description: Human-readable description for MCP tool listing.
        input_schema: JSON Schema dict for module input.
        output_schema: JSON Schema dict for module output.
        tags: Categorization tags.
        target: Callable reference in 'module.path:callable' format.
        version: Module version string.
        warnings: Non-fatal issues encountered during scanning.
    """

    module_id: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    tags: list[str]
    target: str
    version: str = "1.0.0"
    warnings: list[str] = field(default_factory=list)


class BaseScanner(ABC):
    """Abstract base class for all scanners.

    Subclasses must implement scan() and get_source_name().
    The filter_modules() utility is provided for include/exclude filtering.
    """

    @abstractmethod
    def scan(
        self,
        include: str | None = None,
        exclude: str | None = None,
    ) -> list[ScannedModule]:
        """Scan endpoints and return module definitions.

        Args:
            include: Regex pattern to include (matches against module_id).
            exclude: Regex pattern to exclude (matches against module_id).

        Returns:
            List of ScannedModule instances.
        """
        ...

    @abstractmethod
    def get_source_name(self) -> str:
        """Return human-readable scanner name (e.g., 'django-ninja')."""
        ...

    def filter_modules(
        self,
        modules: list[ScannedModule],
        include: str | None = None,
        exclude: str | None = None,
    ) -> list[ScannedModule]:
        """Apply include/exclude regex filters to a list of ScannedModules.

        Args:
            modules: List of ScannedModule instances to filter.
            include: If set, only modules whose module_id matches are kept.
            exclude: If set, modules whose module_id matches are removed.

        Returns:
            Filtered list of ScannedModule instances.
        """
        result = modules

        if include is not None:
            pattern = re.compile(include)
            result = [m for m in result if pattern.search(m.module_id)]

        if exclude is not None:
            pattern = re.compile(exclude)
            result = [m for m in result if not pattern.search(m.module_id)]

        return result
```

Update `src/django_apcore/scanners/__init__.py`:

```python
"""Scanner subpackage.

Provides BaseScanner, ScannedModule, and scanner discovery utilities.
"""

from __future__ import annotations

from django_apcore.scanners.base import BaseScanner, ScannedModule

__all__ = ["BaseScanner", "ScannedModule"]


def get_scanner(source: str) -> BaseScanner:
    """Return a scanner instance for the given source.

    Args:
        source: Scanner source identifier ('ninja' or 'drf').

    Returns:
        A BaseScanner subclass instance.

    Raises:
        ValueError: If the source is not recognized.
        ImportError: If the required optional dependency is not installed.
    """
    if source == "ninja":
        from django_apcore.scanners.ninja import NinjaScanner

        return NinjaScanner()
    elif source == "drf":
        from django_apcore.scanners.drf import DRFScanner

        return DRFScanner()
    else:
        raise ValueError(f"Unknown scanner source: '{source}'. Must be 'ninja' or 'drf'.")
```

### Step 4: Run tests -- verify they pass

```bash
pytest tests/test_scanner_base.py -x --tb=short -v
```

All tests should pass.

### Step 5: Commit

```bash
git add src/django_apcore/scanners/ tests/test_scanner_base.py
git commit -m "feat: BaseScanner ABC and ScannedModule dataclass with filtering"
```

## Acceptance Criteria

- [ ] `ScannedModule` dataclass has all 8 fields: `module_id`, `description`, `input_schema`, `output_schema`, `tags`, `target`, `version`, `warnings`
- [ ] `version` defaults to `"1.0.0"` and `warnings` defaults to empty list
- [ ] Each `ScannedModule` instance gets its own `warnings` list (no shared mutable default)
- [ ] `BaseScanner` is abstract -- cannot be instantiated directly
- [ ] Subclasses must implement both `scan()` and `get_source_name()`
- [ ] `filter_modules()` correctly applies include/exclude regex patterns
- [ ] Include filter keeps only matching modules; exclude filter removes matching modules
- [ ] Combined include + exclude works (include first, then exclude)
- [ ] `get_scanner()` factory dispatches to correct scanner class
- [ ] 100% test coverage for `scanners/base.py`

## Dependencies

- **001-setup** -- Requires project structure

## Estimated Time

2 hours

## Troubleshooting

**Issue: `field(default_factory=list)` causes mutable default warning from ruff**
This is the correct pattern for mutable defaults in dataclasses. Ruff rule B006 should not trigger here because `field(default_factory=...)` is the idiomatic solution. If ruff flags it, verify the rule is correctly configured.

**Issue: `re.compile(include)` raises `re.error` for invalid patterns**
The base class does not validate regex patterns -- that responsibility belongs to the management command argument parsing. If you want defensive handling, catch `re.error` and re-raise with a descriptive message.

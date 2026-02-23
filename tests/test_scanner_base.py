# tests/test_scanner_base.py
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
            "annotations",
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

    def test_annotations_field_exists(self):
        """ScannedModule has an annotations field."""
        from django_apcore.scanners.base import ScannedModule

        module = ScannedModule(
            module_id="test",
            description="test",
            input_schema={},
            output_schema={},
            tags=[],
            target="mod:func",
            annotations={"deprecated": True},
        )
        assert module.annotations == {"deprecated": True}

    def test_annotations_default_is_none(self):
        """ScannedModule defaults annotations to None."""
        from django_apcore.scanners.base import ScannedModule

        module = ScannedModule(
            module_id="test",
            description="test",
            input_schema={},
            output_schema={},
            tags=[],
            target="mod:func",
        )
        assert module.annotations is None

    def test_warnings_are_independent_instances(self):
        """Each ScannedModule gets its own warnings list (no shared mutable default)."""
        from django_apcore.scanners.base import ScannedModule

        m1 = ScannedModule(
            module_id="m1",
            description="",
            input_schema={},
            output_schema={},
            tags=[],
            target="a:b",
        )
        m2 = ScannedModule(
            module_id="m2",
            description="",
            input_schema={},
            output_schema={},
            tags=[],
            target="a:b",
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
                        input_schema={},
                        output_schema={},
                        tags=["users"],
                        target="app:func",
                    ),
                    ScannedModule(
                        module_id="api.v1.users.create",
                        description="Create user",
                        input_schema={},
                        output_schema={},
                        tags=["users"],
                        target="app:func",
                    ),
                    ScannedModule(
                        module_id="api.v1.products.list",
                        description="List products",
                        input_schema={},
                        output_schema={},
                        tags=["products"],
                        target="app:func",
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

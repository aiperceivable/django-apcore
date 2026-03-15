# tests/test_registry_writer.py
"""Tests for DjangoRegistryWriter, _adapt_view_func, and _schema_to_pydantic."""

from __future__ import annotations

from apcore import Registry
from apcore_toolkit.types import ScannedModule
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# _adapt_view_func
# ---------------------------------------------------------------------------


class TestAdaptViewFunc:
    """Test the _adapt_view_func helper."""

    def test_strips_request_param(self):
        from django_apcore.output.registry_writer import _adapt_view_func

        def my_view(request, task_id: int) -> dict:
            return {"id": task_id}

        adapted = _adapt_view_func(my_view)
        result = adapted(task_id=42)
        assert result == {"id": 42}

    def test_preserves_name_and_module(self):
        from django_apcore.output.registry_writer import _adapt_view_func

        def my_view(request):
            return {}

        adapted = _adapt_view_func(my_view)
        assert adapted.__name__ == "my_view"
        assert adapted.__module__ == my_view.__module__

    def test_preserves_doc(self):
        from django_apcore.output.registry_writer import _adapt_view_func

        def my_view(request):
            """My docstring."""
            return {}

        adapted = _adapt_view_func(my_view)
        assert adapted.__doc__ == "My docstring."

    def test_filters_request_from_annotations(self):
        from django_apcore.output.registry_writer import _adapt_view_func

        def my_view(request, name: str) -> dict:
            return {"name": name}

        adapted = _adapt_view_func(my_view)
        assert "request" not in adapted.__annotations__
        assert "name" in adapted.__annotations__
        assert adapted.__annotations__["return"] is dict

    def test_unwraps_status_tuple(self):
        """django-ninja views return (status_code, data) tuples."""
        from django_apcore.output.registry_writer import _adapt_view_func

        def create_view(request, title: str):
            return 201, {"title": title}

        adapted = _adapt_view_func(create_view)
        result = adapted(title="hello")
        assert result == {"title": "hello"}

    def test_passes_through_non_tuple(self):
        from django_apcore.output.registry_writer import _adapt_view_func

        def list_view(request):
            return [{"id": 1}]

        adapted = _adapt_view_func(list_view)
        result = adapted()
        assert result == [{"id": 1}]


# ---------------------------------------------------------------------------
# _schema_to_pydantic
# ---------------------------------------------------------------------------


class TestSchemaToPydantic:
    """Test the _schema_to_pydantic helper."""

    def test_empty_schema(self):
        from django_apcore.output.registry_writer import _schema_to_pydantic

        model = _schema_to_pydantic("Empty", {"type": "object", "properties": {}})
        assert issubclass(model, BaseModel)
        assert len(model.model_fields) == 0

    def test_required_fields(self):
        from django_apcore.output.registry_writer import _schema_to_pydantic

        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "count": {"type": "integer"},
            },
            "required": ["title"],
        }
        model = _schema_to_pydantic("Test", schema)
        assert issubclass(model, BaseModel)
        assert "title" in model.model_fields
        assert "count" in model.model_fields
        assert model.model_fields["title"].is_required()
        assert not model.model_fields["count"].is_required()

    def test_type_mapping(self):
        from django_apcore.output.registry_writer import _schema_to_pydantic

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "score": {"type": "number"},
                "active": {"type": "boolean"},
                "tags": {"type": "array"},
                "meta": {"type": "object"},
            },
            "required": ["name", "age", "score", "active", "tags", "meta"],
        }
        model = _schema_to_pydantic("TypeTest", schema)
        instance = model(
            name="Alice",
            age=30,
            score=9.5,
            active=True,
            tags=["a"],
            meta={"k": "v"},
        )
        assert instance.name == "Alice"
        assert instance.age == 30

    def test_unknown_type_falls_back_to_any(self):
        from django_apcore.output.registry_writer import _schema_to_pydantic

        schema = {
            "type": "object",
            "properties": {"data": {"type": "unknown_type"}},
            "required": ["data"],
        }
        model = _schema_to_pydantic("AnyTest", schema)
        assert "data" in model.model_fields

    def test_no_properties_key(self):
        from django_apcore.output.registry_writer import _schema_to_pydantic

        model = _schema_to_pydantic("NoProps", {"type": "object"})
        assert issubclass(model, BaseModel)
        assert len(model.model_fields) == 0


# ---------------------------------------------------------------------------
# DjangoRegistryWriter.write
# ---------------------------------------------------------------------------


class TestDjangoRegistryWriter:
    """Test the DjangoRegistryWriter class."""

    def _make_module(
        self, module_id="test.mod", target="tests.test_registry_writer:_dummy_view"
    ):
        return ScannedModule(
            module_id=module_id,
            description="A test module",
            input_schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            output_schema={
                "type": "object",
                "properties": {"id": {"type": "integer"}},
            },
            tags=["test"],
            target=target,
        )

    def test_dry_run_returns_results_without_registering(self):
        from django_apcore.output.registry_writer import DjangoRegistryWriter

        writer = DjangoRegistryWriter()
        registry = Registry()
        modules = [self._make_module()]

        result = writer.write(modules, registry, dry_run=True)

        assert len(result) == 1
        assert result[0].module_id == "test.mod"
        assert registry.count == 0

    def test_write_registers_module(self):
        from django_apcore.output.registry_writer import DjangoRegistryWriter

        writer = DjangoRegistryWriter()
        registry = Registry()
        modules = [self._make_module()]

        result = writer.write(modules, registry)

        assert len(result) == 1
        assert result[0].module_id == "test.mod"
        assert registry.count == 1

    def test_write_replaces_existing_module(self):
        """Should not raise on duplicate — unregisters first."""
        from django_apcore.output.registry_writer import DjangoRegistryWriter

        writer = DjangoRegistryWriter()
        registry = Registry()
        modules = [self._make_module()]

        # Register twice — should not raise
        writer.write(modules, registry)
        result = writer.write(modules, registry)

        assert len(result) == 1
        assert registry.count == 1

    def test_write_with_verify(self):
        from django_apcore.output.registry_writer import DjangoRegistryWriter

        writer = DjangoRegistryWriter()
        registry = Registry()
        modules = [self._make_module()]

        result = writer.write(modules, registry, verify=True)

        assert len(result) == 1
        assert result[0].verified is True

    def test_adapts_view_function_with_request_param(self):
        """View functions with 'request' as first param should be adapted."""
        from django_apcore.output.registry_writer import DjangoRegistryWriter

        writer = DjangoRegistryWriter()
        registry = Registry()
        modules = [self._make_module(target="tests.test_registry_writer:_dummy_view")]

        result = writer.write(modules, registry)
        assert len(result) == 1

        # The registered module should be callable without 'request'
        fm = registry.get("test.mod")
        assert fm is not None

    def test_non_view_function_works(self):
        """Functions without 'request' param should work directly."""
        from django_apcore.output.registry_writer import DjangoRegistryWriter

        writer = DjangoRegistryWriter()
        registry = Registry()
        modules = [
            self._make_module(target="tests.test_registry_writer:_dummy_plain_func")
        ]

        result = writer.write(modules, registry)
        assert len(result) == 1
        assert registry.count == 1


# ---------------------------------------------------------------------------
# Dummy functions used as targets in tests
# ---------------------------------------------------------------------------


def _dummy_view(request, name: str) -> dict:
    """A dummy Django view for testing."""
    return {"name": name}


def _dummy_plain_func(name: str) -> dict:
    """A plain function (no request param) for testing."""
    return {"name": name}

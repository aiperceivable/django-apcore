"""Tests for the Extension adapter layer."""
from __future__ import annotations

from unittest.mock import MagicMock


class TestDjangoDiscoverer:
    """Tests for DjangoDiscoverer implementing apcore Discoverer protocol."""

    def test_implements_discoverer_protocol(self):
        from apcore import Discoverer

        from django_apcore.extensions import DjangoDiscoverer

        settings = MagicMock()
        d = DjangoDiscoverer(settings)
        assert isinstance(d, Discoverer)

    def test_discover_returns_list(self):
        from django_apcore.extensions import DjangoDiscoverer

        settings = MagicMock()
        settings.module_dir = "/nonexistent"
        settings.binding_pattern = "*.binding.yaml"
        d = DjangoDiscoverer(settings)
        result = d.discover([])
        assert isinstance(result, list)


class TestDjangoModuleValidator:
    """Tests for DjangoModuleValidator implementing apcore ModuleValidator protocol."""

    def test_implements_module_validator_protocol(self):
        from apcore import ModuleValidator

        from django_apcore.extensions import DjangoModuleValidator

        v = DjangoModuleValidator()
        assert isinstance(v, ModuleValidator)

    def test_validate_valid_module_returns_empty(self):
        from django_apcore.extensions import DjangoModuleValidator

        v = DjangoModuleValidator()
        module = MagicMock()
        module.module_id = "valid.module"
        errors = v.validate(module)
        assert errors == []

    def test_validate_reserved_word_returns_error(self):
        from django_apcore.extensions import DjangoModuleValidator

        v = DjangoModuleValidator()
        module = MagicMock()
        module.module_id = "system.test"
        errors = v.validate(module)
        assert len(errors) > 0
        assert "reserved" in errors[0].lower()

    def test_validate_long_module_id_returns_error(self):
        from django_apcore.extensions import DjangoModuleValidator

        v = DjangoModuleValidator()
        module = MagicMock()
        module.module_id = "a" * 200
        errors = v.validate(module)
        assert len(errors) > 0
        assert "max length" in errors[0].lower() or "exceeds" in errors[0].lower()

    def test_validate_no_module_id_returns_error(self):
        from django_apcore.extensions import DjangoModuleValidator

        v = DjangoModuleValidator()
        module = MagicMock(spec=[])  # No attributes
        errors = v.validate(module)
        assert len(errors) > 0

    def test_extra_validators_called(self):
        from django_apcore.extensions import DjangoModuleValidator

        extra = MagicMock()
        extra.validate.return_value = ["extra error"]
        v = DjangoModuleValidator(extra_validators=[extra])
        module = MagicMock()
        module.module_id = "valid.module"
        errors = v.validate(module)
        assert "extra error" in errors
        extra.validate.assert_called_once_with(module)

    def test_extra_validator_exception_is_swallowed(self):
        from django_apcore.extensions import DjangoModuleValidator

        extra = MagicMock()
        extra.validate.side_effect = RuntimeError("boom")
        v = DjangoModuleValidator(extra_validators=[extra])
        module = MagicMock()
        module.module_id = "valid.module"
        # Should not raise
        errors = v.validate(module)
        assert errors == []

    def test_validate_multiple_reserved_words(self):
        from django_apcore.extensions import DjangoModuleValidator

        v = DjangoModuleValidator()
        module = MagicMock()
        module.module_id = "system.internal.test"
        errors = v.validate(module)
        assert len(errors) == 2

    def test_validate_reserved_word_and_long_id(self):
        from django_apcore.extensions import DjangoModuleValidator

        v = DjangoModuleValidator()
        module = MagicMock()
        module.module_id = "system." + "a" * 200
        errors = v.validate(module)
        # Should have both reserved word error and length error
        assert len(errors) == 2


class TestSetupExtensions:
    """Tests for setup_extensions() function."""

    def test_returns_extension_manager(self):
        from apcore import ExtensionManager

        from django_apcore.extensions import setup_extensions

        settings = MagicMock()
        settings.middlewares = []
        settings.acl_path = None
        settings.tracing = None
        settings.module_validators = []
        ext_mgr = setup_extensions(settings)
        assert isinstance(ext_mgr, ExtensionManager)

    def test_registers_discoverer(self):
        from django_apcore.extensions import setup_extensions

        settings = MagicMock()
        settings.middlewares = []
        settings.acl_path = None
        settings.tracing = None
        settings.module_validators = []
        ext_mgr = setup_extensions(settings)
        discoverer = ext_mgr.get("discoverer")
        assert discoverer is not None

    def test_registers_module_validator(self):
        from django_apcore.extensions import DjangoModuleValidator, setup_extensions

        settings = MagicMock()
        settings.middlewares = []
        settings.acl_path = None
        settings.tracing = None
        settings.module_validators = []
        ext_mgr = setup_extensions(settings)
        validator = ext_mgr.get("module_validator")
        assert validator is not None
        assert isinstance(validator, DjangoModuleValidator)

    def test_no_acl_when_path_is_none(self):
        from django_apcore.extensions import setup_extensions

        settings = MagicMock()
        settings.middlewares = []
        settings.acl_path = None
        settings.tracing = None
        settings.module_validators = []
        ext_mgr = setup_extensions(settings)
        acl = ext_mgr.get("acl")
        assert acl is None

    def test_no_span_exporter_when_tracing_is_none(self):
        from django_apcore.extensions import setup_extensions

        settings = MagicMock()
        settings.middlewares = []
        settings.acl_path = None
        settings.tracing = None
        settings.module_validators = []
        ext_mgr = setup_extensions(settings)
        exporters = ext_mgr.get_all("span_exporter")
        assert exporters == []


class TestImportAndInstantiate:
    """Tests for _import_and_instantiate helper."""

    def test_valid_import(self):
        from django_apcore.extensions import _import_and_instantiate

        result = _import_and_instantiate("unittest.mock.MagicMock")
        assert result is not None

    def test_invalid_import_returns_none(self):
        from django_apcore.extensions import _import_and_instantiate

        result = _import_and_instantiate("nonexistent.module.Class")
        assert result is None

    def test_bad_dotted_path_returns_none(self):
        from django_apcore.extensions import _import_and_instantiate

        result = _import_and_instantiate("nodots")
        assert result is None


class TestBuildSpanExporter:
    """Tests for _build_span_exporter helper."""

    def test_true_returns_stdout_exporter(self):
        from apcore import StdoutExporter

        from django_apcore.extensions import _build_span_exporter

        exporter = _build_span_exporter(True)
        assert isinstance(exporter, StdoutExporter)

    def test_dict_stdout(self):
        from apcore import StdoutExporter

        from django_apcore.extensions import _build_span_exporter

        exporter = _build_span_exporter({"exporter": "stdout"})
        assert isinstance(exporter, StdoutExporter)

    def test_dict_in_memory(self):
        from apcore import InMemoryExporter

        from django_apcore.extensions import _build_span_exporter

        exporter = _build_span_exporter({"exporter": "in_memory"})
        assert isinstance(exporter, InMemoryExporter)

    def test_false_returns_none(self):
        from django_apcore.extensions import _build_span_exporter

        exporter = _build_span_exporter(False)
        assert exporter is None

"""Tests for the explorer web views and API endpoints."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory, override_settings

from django_apcore.web.api import call_module, get_module, list_modules
from django_apcore.web.views import explorer_page


@pytest.fixture()
def rf():
    return RequestFactory()


def _make_mock_module(module_id, description="", tags=None, metadata=None, version="1.0.0"):
    """Create a mock module object."""
    m = MagicMock()
    m.module_id = module_id
    m.description = description
    m.tags = tags or []
    m.metadata = metadata or {}
    m.version = version
    return m


def _make_mock_descriptor(
    module_id,
    description="",
    documentation="",
    tags=None,
    version="1.0.0",
    annotations=None,
    metadata=None,
    input_schema=None,
    output_schema=None,
):
    """Create a mock ModuleDescriptor."""
    d = MagicMock()
    d.module_id = module_id
    d.description = description
    d.documentation = documentation
    d.tags = tags or []
    d.version = version
    d.annotations = annotations
    d.metadata = metadata or {}
    d.input_schema = input_schema or {}
    d.output_schema = output_schema or {}
    return d


class TestExplorerPage:
    """Test the HTML explorer page."""

    def test_returns_html(self, rf):
        request = rf.get("/apcore/")
        response = explorer_page(request)
        assert response.status_code == 200
        assert response["Content-Type"] == "text/html"

    def test_contains_title(self, rf):
        request = rf.get("/apcore/")
        response = explorer_page(request)
        content = response.content.decode()
        assert "apcore Explorer" in content

    def test_contains_javascript(self, rf):
        request = rf.get("/apcore/")
        response = explorer_page(request)
        content = response.content.decode()
        assert "fetch(" in content
        assert "loadDetail" in content
        assert "execModule" in content


class TestListModules:
    """Test GET /modules/ endpoint."""

    @patch("django_apcore.web.api.get_registry")
    def test_empty_registry(self, mock_reg, rf):
        registry = MagicMock()
        registry.iter.return_value = iter([])
        mock_reg.return_value = registry

        request = rf.get("/apcore/modules/")
        response = list_modules(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data == []

    @patch("django_apcore.web.api.get_registry")
    def test_returns_modules(self, mock_reg, rf):
        mod1 = _make_mock_module("hello", description="Greet someone", tags=["demo"])
        mod2 = _make_mock_module("math.add", description="Add numbers")
        registry = MagicMock()
        registry.iter.return_value = iter([("hello", mod1), ("math.add", mod2)])
        mock_reg.return_value = registry

        request = rf.get("/apcore/modules/")
        response = list_modules(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 2
        assert data[0]["module_id"] == "hello"
        assert data[0]["description"] == "Greet someone"
        assert data[0]["tags"] == ["demo"]
        assert data[1]["module_id"] == "math.add"

    @patch("django_apcore.web.api.get_registry")
    def test_module_metadata_fields(self, mock_reg, rf):
        mod = _make_mock_module(
            "test",
            metadata={"http_method": "POST", "url_rule": "/api/test/"},
            version="2.0.0",
        )
        registry = MagicMock()
        registry.iter.return_value = iter([("test", mod)])
        mock_reg.return_value = registry

        request = rf.get("/apcore/modules/")
        response = list_modules(request)
        data = json.loads(response.content)
        assert data[0]["http_method"] == "POST"
        assert data[0]["url_rule"] == "/api/test/"
        assert data[0]["version"] == "2.0.0"

    def test_rejects_post(self, rf):
        request = rf.post("/apcore/modules/")
        response = list_modules(request)
        assert response.status_code == 405


class TestGetModule:
    """Test GET /modules/<module_id>/ endpoint."""

    @patch("django_apcore.web.api.get_registry")
    def test_returns_module_detail(self, mock_reg, rf):
        descriptor = _make_mock_descriptor(
            "hello",
            description="Greet someone",
            documentation="Greet someone by name",
            tags=["demo"],
            input_schema={"type": "object", "properties": {"name": {"type": "string"}}},
            output_schema={"type": "object"},
        )
        registry = MagicMock()
        registry.get_definition.return_value = descriptor
        mock_reg.return_value = registry

        request = rf.get("/apcore/modules/hello/")
        response = get_module(request, "hello")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["module_id"] == "hello"
        assert data["description"] == "Greet someone"
        assert data["documentation"] == "Greet someone by name"
        assert data["tags"] == ["demo"]
        assert data["input_schema"]["properties"]["name"]["type"] == "string"

    @patch("django_apcore.web.api.get_registry")
    def test_module_not_found(self, mock_reg, rf):
        registry = MagicMock()
        registry.get_definition.return_value = None
        mock_reg.return_value = registry

        request = rf.get("/apcore/modules/nonexistent/")
        response = get_module(request, "nonexistent")
        assert response.status_code == 404
        data = json.loads(response.content)
        assert "not found" in data["error"]

    @patch("django_apcore.web.api.get_registry")
    def test_annotations_dict(self, mock_reg, rf):
        descriptor = _make_mock_descriptor(
            "test", annotations={"readOnly": True, "destructive": False}
        )
        registry = MagicMock()
        registry.get_definition.return_value = descriptor
        mock_reg.return_value = registry

        request = rf.get("/apcore/modules/test/")
        response = get_module(request, "test")
        data = json.loads(response.content)
        assert data["annotations"] == {"readOnly": True, "destructive": False}

    @patch("django_apcore.web.api.get_registry")
    def test_dotted_module_id(self, mock_reg, rf):
        descriptor = _make_mock_descriptor("math.add")
        registry = MagicMock()
        registry.get_definition.return_value = descriptor
        mock_reg.return_value = registry

        request = rf.get("/apcore/modules/math.add/")
        response = get_module(request, "math.add")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["module_id"] == "math.add"


class TestCallModule:
    """Test POST /modules/<module_id>/call/ endpoint."""

    @override_settings(APCORE_EXPLORER_ALLOW_EXECUTE=False)
    @patch("django_apcore.web.api.get_apcore_settings")
    def test_execute_disabled(self, mock_settings, rf):
        settings = MagicMock()
        settings.explorer_allow_execute = False
        mock_settings.return_value = settings

        request = rf.post(
            "/apcore/modules/hello/call/",
            data=json.dumps({"name": "World"}),
            content_type="application/json",
        )
        response = call_module(request, "hello")
        assert response.status_code == 403
        data = json.loads(response.content)
        assert "disabled" in data["error"]

    @patch("django_apcore.web.api.get_context_factory")
    @patch("django_apcore.web.api.get_executor")
    @patch("django_apcore.web.api.get_apcore_settings")
    def test_execute_success(self, mock_settings, mock_get_exec, mock_cf, rf):
        settings = MagicMock()
        settings.explorer_allow_execute = True
        mock_settings.return_value = settings

        executor = MagicMock()
        executor.call.return_value = {"message": "Hello, World!"}
        mock_get_exec.return_value = executor

        factory = MagicMock()
        factory.create_context.return_value = MagicMock()
        mock_cf.return_value = factory

        request = rf.post(
            "/apcore/modules/hello/call/",
            data=json.dumps({"name": "World"}),
            content_type="application/json",
        )
        response = call_module(request, "hello")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["output"]["message"] == "Hello, World!"

    @patch("django_apcore.web.api.get_context_factory")
    @patch("django_apcore.web.api.get_executor")
    @patch("django_apcore.web.api.get_apcore_settings")
    def test_module_not_found(self, mock_settings, mock_get_exec, mock_cf, rf):
        from apcore.errors import ModuleNotFoundError as ApcoreNotFound

        settings = MagicMock()
        settings.explorer_allow_execute = True
        mock_settings.return_value = settings

        executor = MagicMock()
        executor.call.side_effect = ApcoreNotFound("nonexistent")
        mock_get_exec.return_value = executor

        factory = MagicMock()
        factory.create_context.return_value = MagicMock()
        mock_cf.return_value = factory

        request = rf.post(
            "/apcore/modules/nonexistent/call/",
            data=json.dumps({}),
            content_type="application/json",
        )
        response = call_module(request, "nonexistent")
        assert response.status_code == 404

    @patch("django_apcore.web.api.get_context_factory")
    @patch("django_apcore.web.api.get_executor")
    @patch("django_apcore.web.api.get_apcore_settings")
    def test_validation_error(self, mock_settings, mock_get_exec, mock_cf, rf):
        from apcore.errors import SchemaValidationError

        settings = MagicMock()
        settings.explorer_allow_execute = True
        mock_settings.return_value = settings

        executor = MagicMock()
        executor.call.side_effect = SchemaValidationError("invalid input")
        mock_get_exec.return_value = executor

        factory = MagicMock()
        factory.create_context.return_value = MagicMock()
        mock_cf.return_value = factory

        request = rf.post(
            "/apcore/modules/hello/call/",
            data=json.dumps({"bad": "input"}),
            content_type="application/json",
        )
        response = call_module(request, "hello")
        assert response.status_code == 400

    @patch("django_apcore.web.api.get_context_factory")
    @patch("django_apcore.web.api.get_executor")
    @patch("django_apcore.web.api.get_apcore_settings")
    def test_empty_body(self, mock_settings, mock_get_exec, mock_cf, rf):
        settings = MagicMock()
        settings.explorer_allow_execute = True
        mock_settings.return_value = settings

        executor = MagicMock()
        executor.call.return_value = {"result": "ok"}
        mock_get_exec.return_value = executor

        factory = MagicMock()
        factory.create_context.return_value = MagicMock()
        mock_cf.return_value = factory

        request = rf.post(
            "/apcore/modules/hello/call/",
            content_type="application/json",
        )
        response = call_module(request, "hello")
        assert response.status_code == 200

    @patch("django_apcore.web.api.get_context_factory")
    @patch("django_apcore.web.api.get_executor")
    @patch("django_apcore.web.api.get_apcore_settings")
    def test_server_error(self, mock_settings, mock_get_exec, mock_cf, rf):
        settings = MagicMock()
        settings.explorer_allow_execute = True
        mock_settings.return_value = settings

        executor = MagicMock()
        executor.call.side_effect = RuntimeError("Something went wrong")
        mock_get_exec.return_value = executor

        factory = MagicMock()
        factory.create_context.return_value = MagicMock()
        mock_cf.return_value = factory

        request = rf.post(
            "/apcore/modules/hello/call/",
            data=json.dumps({}),
            content_type="application/json",
        )
        response = call_module(request, "hello")
        assert response.status_code == 500

    def test_rejects_get(self, rf):
        request = rf.get("/apcore/modules/hello/call/")
        response = call_module(request, "hello")
        assert response.status_code == 405

    @patch("django_apcore.web.api.get_apcore_settings")
    def test_invalid_json_body(self, mock_settings, rf):
        settings = MagicMock()
        settings.explorer_allow_execute = True
        mock_settings.return_value = settings

        request = rf.post(
            "/apcore/modules/hello/call/",
            data="not-valid-json{",
            content_type="application/json",
        )
        response = call_module(request, "hello")
        assert response.status_code == 400
        data = json.loads(response.content)
        assert "Invalid JSON" in data["error"]


class TestExplorerSettings:
    """Test APCORE_EXPLORER_* settings validation."""

    def test_default_explorer_disabled(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_enabled is False

    def test_default_explorer_url_prefix(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_url_prefix == "/apcore"

    def test_default_explorer_allow_execute(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_allow_execute is False

    @override_settings(APCORE_EXPLORER_ENABLED=True)
    def test_explorer_enabled_true(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_enabled is True

    @override_settings(APCORE_EXPLORER_URL_PREFIX="/browse")
    def test_custom_url_prefix(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_url_prefix == "/browse"

    @override_settings(APCORE_EXPLORER_ALLOW_EXECUTE=True)
    def test_allow_execute_true(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.explorer_allow_execute is True

    @override_settings(APCORE_EXPLORER_ENABLED="yes")
    def test_explorer_enabled_invalid_type(self):
        from django.core.exceptions import ImproperlyConfigured

        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_EXPLORER_ENABLED"):
            get_apcore_settings()

    @override_settings(APCORE_EXPLORER_URL_PREFIX="")
    def test_url_prefix_empty_rejected(self):
        from django.core.exceptions import ImproperlyConfigured

        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_EXPLORER_URL_PREFIX"):
            get_apcore_settings()

    @override_settings(APCORE_EXPLORER_URL_PREFIX=123)
    def test_url_prefix_invalid_type(self):
        from django.core.exceptions import ImproperlyConfigured

        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_EXPLORER_URL_PREFIX"):
            get_apcore_settings()

    @override_settings(APCORE_EXPLORER_ALLOW_EXECUTE="true")
    def test_allow_execute_invalid_type(self):
        from django.core.exceptions import ImproperlyConfigured

        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_EXPLORER_ALLOW_EXECUTE"):
            get_apcore_settings()


class TestMakeSerializable:
    """Test the _make_serializable helper."""

    def test_plain_dict(self):
        from django_apcore.web.api import _make_serializable

        result = _make_serializable({"key": "value"})
        assert result == {"key": "value"}

    def test_pydantic_model(self):
        from django_apcore.web.api import _make_serializable

        mock_model = MagicMock()
        mock_model.model_dump.return_value = {"field": 42}
        result = _make_serializable(mock_model)
        assert result == {"field": 42}

    def test_nested_list(self):
        from django_apcore.web.api import _make_serializable

        result = _make_serializable([{"a": 1}, {"b": 2}])
        assert result == [{"a": 1}, {"b": 2}]

    def test_primitive(self):
        from django_apcore.web.api import _make_serializable

        assert _make_serializable("hello") == "hello"
        assert _make_serializable(42) == 42


class TestAnnotationsToDict:
    """Test the _annotations_to_dict helper."""

    def test_none_returns_none(self):
        from django_apcore.web.api import _annotations_to_dict

        assert _annotations_to_dict(None) is None

    def test_dict_passthrough(self):
        from django_apcore.web.api import _annotations_to_dict

        result = _annotations_to_dict({"readOnly": True})
        assert result == {"readOnly": True}

    def test_unknown_type_returns_none(self):
        from django_apcore.web.api import _annotations_to_dict

        assert _annotations_to_dict("not a dict") is None


class TestExplorerUrlPatterns:
    """Test the URL configuration module."""

    def test_urlpatterns_exist(self):
        from django_apcore.urls import explorer_urlpatterns

        assert len(explorer_urlpatterns) == 4

    def test_urlpatterns_names(self):
        from django_apcore.urls import explorer_urlpatterns

        names = [p.name for p in explorer_urlpatterns]
        assert "explorer" in names
        assert "list-modules" in names
        assert "module-detail" in names
        assert "call-module" in names

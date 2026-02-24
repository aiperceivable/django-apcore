"""Functional tests for the demo project.

Runs within the demo's own Django environment (configured by example/conftest.py).
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import Client


# ---------------------------------------------------------------------------
# Module function unit tests (calling decorated functions directly)
# ---------------------------------------------------------------------------

class TestHelloWorldModule:
    def test_default_greeting(self):
        from demo.apcore_modules.hello import hello_world

        result = hello_world()
        assert result == {"message": "Hello, World!"}

    def test_custom_name(self):
        from demo.apcore_modules.hello import hello_world

        result = hello_world(name="Django")
        assert result == {"message": "Hello, Django!"}


class TestAddModule:
    def test_add(self):
        from demo.apcore_modules.math_tools import add

        result = add(a=10, b=32)
        assert result == {"result": 42}


class TestMultiplyModule:
    def test_multiply(self):
        from demo.apcore_modules.math_tools import multiply

        result = multiply(a=7, b=6)
        assert result == {"result": 42}


class TestSlowProcessModule:
    def test_immediate_return(self):
        from demo.apcore_modules.slow_task import slow_process

        result = slow_process(seconds=0)
        assert result == {"message": "Completed after 0 seconds"}


# ---------------------------------------------------------------------------
# Django view tests
# ---------------------------------------------------------------------------

class TestHelloView:
    @pytest.fixture()
    def client(self):
        return Client()

    @patch("demo.views.executor_call")
    def test_get_hello_default(self, mock_exec, client):
        mock_exec.return_value = {"message": "Hello, World!"}
        resp = client.get("/api/hello/")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["message"] == "Hello, World!"
        mock_exec.assert_called_once()

    @patch("demo.views.executor_call")
    def test_get_hello_with_name(self, mock_exec, client):
        mock_exec.return_value = {"message": "Hello, Django!"}
        resp = client.get("/api/hello/?name=Django")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["message"] == "Hello, Django!"

    def test_post_not_allowed(self, client):
        resp = client.post("/api/hello/")
        assert resp.status_code == 405


class TestAddView:
    @pytest.fixture()
    def client(self):
        return Client()

    @patch("demo.views.executor_call")
    def test_post_add(self, mock_exec, client):
        mock_exec.return_value = {"result": 42}
        resp = client.post(
            "/api/add/",
            data=json.dumps({"a": 10, "b": 32}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["result"] == 42

    def test_get_not_allowed(self, client):
        resp = client.get("/api/add/")
        assert resp.status_code == 405


class TestMultiplyView:
    @pytest.fixture()
    def client(self):
        return Client()

    @patch("demo.views.executor_call")
    def test_post_multiply(self, mock_exec, client):
        mock_exec.return_value = {"result": 42}
        resp = client.post(
            "/api/multiply/",
            data=json.dumps({"a": 7, "b": 6}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["result"] == 42


class TestTaskStatusView:
    @pytest.fixture()
    def client(self):
        return Client()

    @patch("demo.views.get_task_status")
    def test_task_not_found(self, mock_status, client):
        mock_status.return_value = None
        resp = client.get("/api/tasks/nonexistent-id/status/")
        assert resp.status_code == 404
        data = json.loads(resp.content)
        assert data["error"] == "Task not found"


class TestListModulesView:
    @pytest.fixture()
    def client(self):
        return Client()

    @patch("demo.views.get_registry")
    def test_list_modules(self, mock_registry, client):
        mock_reg = MagicMock()
        mock_reg.count = 4
        mock_registry.return_value = mock_reg
        resp = client.get("/api/modules/")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["module_count"] == 4


# ---------------------------------------------------------------------------
# Module discovery test
# ---------------------------------------------------------------------------

class TestModuleDiscovery:
    def test_apcore_modules_importable(self):
        import demo.apcore_modules as mod

        assert mod is not None

    def test_four_decorated_functions(self):
        import demo.apcore_modules as mod

        decorated = [
            name
            for name in dir(mod)
            if callable(getattr(mod, name))
            and hasattr(getattr(mod, name), "apcore_module")
        ]
        assert len(decorated) == 4
        assert set(decorated) == {"hello_world", "add", "multiply", "slow_process"}

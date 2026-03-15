"""Functional tests for the demo project.

Runs within the demo's own Django environment (configured by example/conftest.py).
"""

import json

import pytest
from demo.api import _tasks
from django.test import Client

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SEED_TASKS = {
    1: {
        "id": 1,
        "title": "Try django-apcore",
        "description": "Run the demo",
        "done": False,
    },
    2: {
        "id": 2,
        "title": "Connect MCP client",
        "description": "Use Claude Desktop",
        "done": False,
    },
}


def _reset_store():
    """Reset the in-memory task store to seed state."""
    import demo.api as api_mod

    api_mod._tasks.clear()
    api_mod._tasks.update({k: dict(v) for k, v in SEED_TASKS.items()})
    api_mod._next_id = 3


# ---------------------------------------------------------------------------
# DjangoApcore unified entry point tests
# ---------------------------------------------------------------------------


class TestDjangoApcoreEntryPoint:
    """Test the DjangoApcore unified class in the demo context."""

    def test_import(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        assert app is not None

    def test_singleton(self):
        from django_apcore import DjangoApcore

        DjangoApcore._reset_instance()
        try:
            a = DjangoApcore.get_instance()
            b = DjangoApcore.get_instance()
            assert a is b
        finally:
            DjangoApcore._reset_instance()

    def test_settings_accessible(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        assert app.settings.server_name == "task-manager-mcp"
        assert app.settings.serve_port == 9090

    def test_scan_ninja(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        modules = app.scan(source="ninja")
        ids = [m.module_id for m in modules]
        assert len(ids) >= 5
        # Verify annotations are inferred
        for m in modules:
            assert m.annotations is not None

    def test_scan_with_include_filter(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        modules = app.scan(source="ninja", include=r"tasks")
        assert len(modules) >= 1
        assert all("tasks" in m.module_id for m in modules)

    def test_scan_with_exclude_filter(self):
        from django_apcore import DjangoApcore

        app = DjangoApcore()
        all_modules = app.scan(source="ninja")
        filtered = app.scan(source="ninja", exclude=r"_2$")
        assert len(filtered) < len(all_modules)


# ---------------------------------------------------------------------------
# Module function unit tests
# ---------------------------------------------------------------------------


class TestTaskStatsModule:
    def setup_method(self):
        _reset_store()

    def test_stats_with_seed_data(self):
        from demo.apcore_modules.task_stats import task_stats

        result = task_stats()
        assert result == {"total": 2, "done": 0, "pending": 2}

    def test_stats_with_done_task(self):
        from demo.apcore_modules.task_stats import task_stats

        _tasks[1]["done"] = True
        result = task_stats()
        assert result == {"total": 2, "done": 1, "pending": 1}

    def test_stats_empty_store(self):
        from demo.apcore_modules.task_stats import task_stats

        _tasks.clear()
        result = task_stats()
        assert result == {"total": 0, "done": 0, "pending": 0}


# ---------------------------------------------------------------------------
# django-ninja integration tests (real HTTP, no mocks)
# ---------------------------------------------------------------------------


class TestListTasks:
    def setup_method(self):
        _reset_store()

    @pytest.fixture()
    def client(self):
        return Client()

    def test_list_returns_seed_tasks(self, client):
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert len(data) == 2
        assert data[0]["title"] == "Try django-apcore"


class TestCreateTask:
    def setup_method(self):
        _reset_store()

    @pytest.fixture()
    def client(self):
        return Client()

    def test_create_returns_201(self, client):
        resp = client.post(
            "/api/tasks",
            data=json.dumps({"title": "New task", "description": "A test"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = json.loads(resp.content)
        assert data["title"] == "New task"
        assert data["id"] == 3
        assert data["done"] is False

    def test_create_adds_to_store(self, client):
        client.post(
            "/api/tasks",
            data=json.dumps({"title": "Another"}),
            content_type="application/json",
        )
        assert len(_tasks) == 3


class TestGetTask:
    def setup_method(self):
        _reset_store()

    @pytest.fixture()
    def client(self):
        return Client()

    def test_get_existing_task(self, client):
        resp = client.get("/api/tasks/1")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["id"] == 1
        assert data["title"] == "Try django-apcore"

    def test_get_nonexistent_returns_404(self, client):
        resp = client.get("/api/tasks/999")
        assert resp.status_code == 404
        data = json.loads(resp.content)
        assert data["detail"] == "not found"


class TestUpdateTask:
    def setup_method(self):
        _reset_store()

    @pytest.fixture()
    def client(self):
        return Client()

    def test_update_title(self, client):
        resp = client.put(
            "/api/tasks/1",
            data=json.dumps({"title": "Updated title"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["title"] == "Updated title"
        assert data["description"] == "Run the demo"  # unchanged

    def test_mark_done(self, client):
        resp = client.put(
            "/api/tasks/1",
            data=json.dumps({"done": True}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["done"] is True

    def test_update_nonexistent_returns_404(self, client):
        resp = client.put(
            "/api/tasks/999",
            data=json.dumps({"title": "Nope"}),
            content_type="application/json",
        )
        assert resp.status_code == 404


class TestDeleteTask:
    def setup_method(self):
        _reset_store()

    @pytest.fixture()
    def client(self):
        return Client()

    def test_delete_existing_task(self, client):
        resp = client.delete("/api/tasks/1")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["deleted"] is True
        assert 1 not in _tasks

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/api/tasks/999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Module discovery test
# ---------------------------------------------------------------------------


class TestModuleDiscovery:
    def test_apcore_modules_importable(self):
        import demo.apcore_modules as mod

        assert mod is not None

    def test_task_stats_module_registered(self):
        """task_stats.v1 is self-registering via @app.module() decorator."""
        from demo.apcore_modules.task_stats import task_stats

        assert callable(task_stats)
        assert hasattr(task_stats, "apcore_module")
        assert task_stats.apcore_module.module_id == "task_stats.v1"

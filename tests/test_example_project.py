"""Static validation tests for the example/ demo project.

These tests verify file structure, syntax, and configuration without
needing the demo Django environment to be running.
"""

import ast
from pathlib import Path

import pytest
import yaml

EXAMPLE_DIR = Path(__file__).resolve().parent.parent / "example"

REQUIRED_FILES = [
    "Dockerfile",
    "docker-compose.yml",
    "manage.py",
    "README.md",
    ".gitignore",
    "demo/__init__.py",
    "demo/settings.py",
    "demo/urls.py",
    "demo/views.py",
    "demo/apcore_modules/__init__.py",
    "demo/apcore_modules/hello.py",
    "demo/apcore_modules/math_tools.py",
    "demo/apcore_modules/slow_task.py",
]


class TestFileStructure:
    """Verify all expected demo project files exist."""

    @pytest.mark.parametrize("rel_path", REQUIRED_FILES)
    def test_required_file_exists(self, rel_path):
        path = EXAMPLE_DIR / rel_path
        assert path.exists(), f"Missing required file: {rel_path}"


class TestPythonSyntax:
    """Verify all .py files parse without syntax errors."""

    @pytest.fixture(
        params=sorted(EXAMPLE_DIR.rglob("*.py")),
        ids=lambda p: str(p.relative_to(EXAMPLE_DIR)),
    )
    def py_file(self, request):
        return request.param

    def test_python_syntax_valid(self, py_file):
        source = py_file.read_text(encoding="utf-8")
        ast.parse(source, filename=str(py_file))


class TestDockerfile:
    """Verify Dockerfile contains required instructions."""

    @pytest.fixture()
    def dockerfile_content(self):
        return (EXAMPLE_DIR / "Dockerfile").read_text(encoding="utf-8")

    @pytest.mark.parametrize(
        "instruction", ["FROM", "COPY", "RUN pip install", "WORKDIR"]
    )
    def test_dockerfile_has_instruction(self, dockerfile_content, instruction):
        assert (
            instruction in dockerfile_content
        ), f"Dockerfile missing instruction: {instruction}"


class TestDockerCompose:
    """Verify docker-compose.yml structure."""

    @pytest.fixture()
    def compose(self):
        content = (EXAMPLE_DIR / "docker-compose.yml").read_text(encoding="utf-8")
        return yaml.safe_load(content)

    def test_parseable(self, compose):
        assert isinstance(compose, dict)

    def test_has_web_service(self, compose):
        assert "web" in compose["services"]

    def test_has_mcp_service(self, compose):
        assert "mcp" in compose["services"]

    def test_web_port_mapping(self, compose):
        ports = compose["services"]["web"]["ports"]
        assert "8000:8000" in ports

    def test_mcp_port_mapping(self, compose):
        ports = compose["services"]["mcp"]["ports"]
        assert "9090:9090" in ports


class TestSettingsFile:
    """Verify settings.py configuration."""

    @pytest.fixture()
    def settings_source(self):
        return (EXAMPLE_DIR / "demo" / "settings.py").read_text(encoding="utf-8")

    def test_database_engine_correct(self, settings_source):
        assert (
            "django.db.backends.sqlite3" in settings_source
        ), "DATABASE ENGINE should be 'django.db.backends.sqlite3'"


class TestModulesInit:
    """Verify apcore_modules/__init__.py exports."""

    @pytest.fixture()
    def init_source(self):
        return (EXAMPLE_DIR / "demo" / "apcore_modules" / "__init__.py").read_text(
            encoding="utf-8"
        )

    @pytest.mark.parametrize(
        "func_name", ["hello_world", "add", "multiply", "slow_process"]
    )
    def test_exports_function(self, init_source, func_name):
        assert (
            func_name in init_source
        ), f"apcore_modules/__init__.py should export {func_name}"


class TestUrlsFile:
    """Verify urls.py defines the expected routes."""

    @pytest.fixture()
    def urls_source(self):
        return (EXAMPLE_DIR / "demo" / "urls.py").read_text(encoding="utf-8")

    @pytest.mark.parametrize(
        "route",
        [
            "api/hello/",
            "api/add/",
            "api/multiply/",
            "api/tasks/submit/",
            "api/tasks/<str:task_id>/status/",
            "api/modules/",
        ],
    )
    def test_has_route(self, urls_source, route):
        assert route in urls_source, f"urls.py missing route: {route}"

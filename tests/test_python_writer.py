# tests/test_python_writer.py
import ast

import pytest


@pytest.fixture
def sample_modules():
    from django_apcore.scanners.base import ScannedModule

    return [
        ScannedModule(
            module_id="api.v1.users.list",
            description="List all users.",
            input_schema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "limit": {"type": "integer"},
                },
                "required": [],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "items": {"type": "array"},
                    "total": {"type": "integer"},
                },
                "required": ["items", "total"],
            },
            tags=["users"],
            target="myapp.api:list_users",
        ),
    ]


class TestPythonWriter:
    """Test Python @module code generation."""

    def test_write_creates_file(self, tmp_path, sample_modules):
        from django_apcore.output.python_writer import PythonWriter

        writer = PythonWriter()
        writer.write(sample_modules, str(tmp_path))

        py_files = list(tmp_path.glob("*.py"))
        assert len(py_files) >= 1

    def test_generated_code_is_valid_python(self, tmp_path, sample_modules):
        from django_apcore.output.python_writer import PythonWriter

        writer = PythonWriter()
        writer.write(sample_modules, str(tmp_path))

        for py_file in tmp_path.glob("*.py"):
            content = py_file.read_text()
            # Should parse without SyntaxError
            ast.parse(content)

    def test_generated_code_has_module_decorator(self, tmp_path, sample_modules):
        from django_apcore.output.python_writer import PythonWriter

        writer = PythonWriter()
        writer.write(sample_modules, str(tmp_path))

        py_file = list(tmp_path.glob("*.py"))[0]
        content = py_file.read_text()
        assert "@module(" in content
        assert "id='api.v1.users.list'" in content

    def test_generated_code_has_header(self, tmp_path, sample_modules):
        from django_apcore.output.python_writer import PythonWriter

        writer = PythonWriter()
        writer.write(sample_modules, str(tmp_path))

        py_file = list(tmp_path.glob("*.py"))[0]
        content = py_file.read_text()
        assert "Auto-generated" in content
        assert "from __future__ import annotations" in content

    def test_write_creates_directory_if_missing(self, tmp_path, sample_modules):
        from django_apcore.output.python_writer import PythonWriter

        output_dir = tmp_path / "new_dir"
        writer = PythonWriter()
        writer.write(sample_modules, str(output_dir))

        assert output_dir.exists()

    def test_write_empty_list(self, tmp_path):
        from django_apcore.output.python_writer import PythonWriter

        writer = PythonWriter()
        writer.write([], str(tmp_path))

        py_files = list(tmp_path.glob("*.py"))
        assert len(py_files) == 0

    def test_dry_run_does_not_write(self, tmp_path, sample_modules):
        from django_apcore.output.python_writer import PythonWriter

        writer = PythonWriter()
        result = writer.write(sample_modules, str(tmp_path), dry_run=True)

        py_files = list(tmp_path.glob("*.py"))
        assert len(py_files) == 0
        assert len(result) >= 1

    def test_imports_apcore_module(self, tmp_path, sample_modules):
        from django_apcore.output.python_writer import PythonWriter

        writer = PythonWriter()
        writer.write(sample_modules, str(tmp_path))

        py_file = list(tmp_path.glob("*.py"))[0]
        content = py_file.read_text()
        assert "from apcore import module" in content

    def test_annotations_included_when_set(self, tmp_path):
        from django_apcore.output.python_writer import PythonWriter
        from django_apcore.scanners.base import ScannedModule

        module = ScannedModule(
            module_id="api.v1.users.list",
            description="List users",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object", "properties": {}},
            tags=["users"],
            target="myapp.api:list_users",
            annotations={"deprecated": True},
        )

        writer = PythonWriter()
        writer.write([module], str(tmp_path))

        py_file = list(tmp_path.glob("*.py"))[0]
        content = py_file.read_text()
        assert "annotations=" in content
        assert "'deprecated': True" in content

    def test_annotations_omitted_when_none(self, tmp_path, sample_modules):
        from django_apcore.output.python_writer import PythonWriter

        writer = PythonWriter()
        writer.write(sample_modules, str(tmp_path))

        py_file = list(tmp_path.glob("*.py"))[0]
        content = py_file.read_text()
        assert "annotations=" not in content

    def test_invalid_target_module_path_rejected(self, tmp_path):
        from django_apcore.output.python_writer import PythonWriter
        from django_apcore.scanners.base import ScannedModule

        module = ScannedModule(
            module_id="bad.module",
            description="Bad target",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object", "properties": {}},
            tags=[],
            target="os; import sys:func",
        )

        writer = PythonWriter()
        with pytest.raises(ValueError, match="Invalid module path"):
            writer.write([module], str(tmp_path), dry_run=True)

    def test_target_without_colon_rejected(self, tmp_path):
        from django_apcore.output.python_writer import PythonWriter
        from django_apcore.scanners.base import ScannedModule

        module = ScannedModule(
            module_id="bad.module",
            description="Missing colon",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object", "properties": {}},
            tags=[],
            target="users_list",
        )

        writer = PythonWriter()
        with pytest.raises(ValueError, match="Invalid target format"):
            writer.write([module], str(tmp_path), dry_run=True)

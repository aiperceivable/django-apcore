# Task 001: Project Scaffold

## Goal

Set up the complete project structure for django-apcore including `pyproject.toml` with all dependency groups, the `src/django_apcore/` package layout, CI configuration, and development tool configs (ruff, mypy). After this task, the project is installable in editable mode and all tooling runs cleanly on the empty package.

## Files Involved

### Create

- `pyproject.toml` -- Build configuration, dependencies, extras, tool configs
- `src/django_apcore/__init__.py` -- Package root with `__version__`
- `src/django_apcore/scanners/__init__.py` -- Scanner subpackage init
- `src/django_apcore/output/__init__.py` -- Output subpackage init
- `src/django_apcore/management/__init__.py` -- Management package init
- `src/django_apcore/management/commands/__init__.py` -- Commands package init
- `tests/__init__.py` -- Test package init
- `tests/conftest.py` -- Shared pytest fixtures and Django settings
- `.github/workflows/ci.yml` -- GitHub Actions CI pipeline
- `ruff.toml` -- Ruff linter/formatter configuration
- `mypy.ini` -- Mypy type checker configuration

### Test

- `tests/test_init.py` -- Verify package imports and version

## Steps

### Step 1: Write tests (TDD -- Red phase)

Create `tests/conftest.py` with a minimal Django settings configuration:

```python
# tests/conftest.py
import django
from django.conf import settings


def pytest_configure():
    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django_apcore",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
    )
    django.setup()
```

Create `tests/test_init.py`:

```python
# tests/test_init.py


def test_package_version_exists():
    """django_apcore exposes a __version__ string."""
    import django_apcore

    assert hasattr(django_apcore, "__version__")
    assert isinstance(django_apcore.__version__, str)
    assert len(django_apcore.__version__) > 0


def test_package_importable():
    """django_apcore can be imported without errors."""
    import django_apcore  # noqa: F401
```

### Step 2: Run tests -- verify they fail

```bash
pytest tests/test_init.py -x --tb=short
```

Expected: `ModuleNotFoundError: No module named 'django_apcore'`

### Step 3: Implement

Create `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "django-apcore"
version = "0.1.0"
description = "Django App that bridges the apcore protocol to the Django ecosystem"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [
    { name = "Engineering Team" },
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: Django",
    "Framework :: Django :: 4.2",
    "Framework :: Django :: 5.0",
    "Framework :: Django :: 5.1",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
dependencies = [
    "django>=4.2",
    "apcore>=0.2.0",
    "pydantic>=2.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
ninja = ["django-ninja>=1.0"]
drf = ["drf-spectacular>=0.27"]
mcp = ["apcore-mcp>=0.1.0"]
all = [
    "django-ninja>=1.0",
    "drf-spectacular>=0.27",
    "apcore-mcp>=0.1.0",
]
dev = [
    "pytest>=8.0",
    "pytest-django>=4.5",
    "ruff>=0.4",
    "mypy>=1.10",
    "django-stubs>=4.2",
]

[tool.hatch.build.targets.wheel]
packages = ["src/django_apcore"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
django_find_project = false
```

Create `src/django_apcore/__init__.py`:

```python
"""django-apcore: Django App bridging the apcore protocol to Django."""

__version__ = "0.1.0"
```

Create all `__init__.py` files for subpackages (empty files).

Create `ruff.toml`:

```toml
target-version = "py310"
line-length = 88
src = ["src", "tests"]

[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "SIM", "TCH"]
ignore = []

[lint.isort]
known-first-party = ["django_apcore"]

[format]
quote-style = "double"
indent-style = "space"
```

Create `mypy.ini`:

```ini
[mypy]
python_version = 3.10
plugins = mypy_django_plugin.main
strict = true
warn_return_any = true
warn_unused_configs = true
namespace_packages = true
explicit_package_bases = true
mypy_path = src

[mypy.plugins.django-stubs]
django_settings_module = tests.conftest

[mypy-apcore.*]
ignore_missing_imports = True

[mypy-apcore_mcp.*]
ignore_missing_imports = True

[mypy-ninja.*]
ignore_missing_imports = True
```

Create `.github/workflows/ci.yml`:

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/
      - run: ruff format --check src/ tests/

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: mypy src/django_apcore/

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
        django-version: ["4.2", "5.0", "5.1"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]" django~=${{ matrix.django-version }}
      - run: pytest tests/ -x --tb=short
```

### Step 4: Run tests -- verify they pass

```bash
pip install -e ".[dev]"
pytest tests/test_init.py -x --tb=short
ruff check src/ tests/
ruff format --check src/ tests/
```

### Step 5: Commit

```bash
git add -A
git commit -m "feat: project scaffold with pyproject.toml, directory structure, CI config"
```

## Acceptance Criteria

- [ ] `pip install -e ".[dev]"` succeeds without errors
- [ ] `import django_apcore` works and `django_apcore.__version__` returns `"0.1.0"`
- [ ] `ruff check src/ tests/` passes with zero violations
- [ ] `ruff format --check src/ tests/` passes
- [ ] `pytest tests/` runs successfully
- [ ] Directory structure matches tech-design Appendix E (all `__init__.py` files present)
- [ ] `pyproject.toml` defines all required extras: `ninja`, `drf`, `mcp`, `all`, `dev`

## Dependencies

None -- this is the first task.

## Estimated Time

3 hours

## Troubleshooting

**Issue: `pip install -e ".[dev]"` fails with "apcore not found"**
The `apcore` package may not yet be published to PyPI. Install from local path or git URL:
```bash
pip install -e /path/to/apcore-python
pip install -e ".[dev]"
```

**Issue: `mypy` reports errors about missing Django stubs**
Ensure `django-stubs` is installed as part of the dev extras. The `mypy.ini` references the `mypy_django_plugin.main` plugin which requires `django-stubs`.

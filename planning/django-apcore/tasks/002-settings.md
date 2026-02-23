# Task 002: ApcoreSettings

## Goal

Implement `ApcoreSettings`, a frozen dataclass that reads and validates all `APCORE_*` settings from `django.conf.settings`, applies defaults, and raises `ImproperlyConfigured` for invalid types or values. Expose `get_apcore_settings()` as the public API for other components to consume validated settings.

## Files Involved

### Create

- `src/django_apcore/settings.py` -- `ApcoreSettings` dataclass and `get_apcore_settings()` function

### Test

- `tests/test_settings.py` -- Unit tests for all settings validation paths

## Steps

### Step 1: Write tests (TDD -- Red phase)

Create `tests/test_settings.py`:

```python
# tests/test_settings.py
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings


class TestApcoreSettingsDefaults:
    """Test that all APCORE_* settings have correct defaults."""

    def test_default_module_dir(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.module_dir == "apcore_modules/"

    def test_default_auto_discover(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.auto_discover is True

    def test_default_serve_transport(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_transport == "stdio"

    def test_default_serve_host(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_host == "127.0.0.1"

    def test_default_serve_port(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_port == 8000

    def test_default_server_name(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.server_name == "apcore-mcp"

    def test_default_binding_pattern(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.binding_pattern == "*.binding.yaml"


class TestApcoreSettingsCustomValues:
    """Test that custom APCORE_* settings are read correctly."""

    @override_settings(APCORE_MODULE_DIR="custom_modules/")
    def test_custom_module_dir(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.module_dir == "custom_modules/"

    @override_settings(APCORE_AUTO_DISCOVER=False)
    def test_custom_auto_discover(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.auto_discover is False

    @override_settings(APCORE_SERVE_TRANSPORT="streamable-http")
    def test_custom_serve_transport(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_transport == "streamable-http"

    @override_settings(APCORE_SERVE_PORT=9090)
    def test_custom_serve_port(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_port == 9090


class TestApcoreSettingsValidation:
    """Test that invalid APCORE_* settings raise ImproperlyConfigured."""

    @override_settings(APCORE_MODULE_DIR=123)
    def test_module_dir_must_be_string(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_MODULE_DIR must be a string path"):
            get_apcore_settings()

    @override_settings(APCORE_AUTO_DISCOVER="true")
    def test_auto_discover_must_be_bool(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_AUTO_DISCOVER must be a boolean"):
            get_apcore_settings()

    @override_settings(APCORE_SERVE_TRANSPORT="websocket")
    def test_serve_transport_must_be_valid_choice(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_SERVE_TRANSPORT must be one of"):
            get_apcore_settings()

    @override_settings(APCORE_SERVE_PORT=99999)
    def test_serve_port_must_be_in_range(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_SERVE_PORT must be an integer between 1 and 65535"):
            get_apcore_settings()

    @override_settings(APCORE_SERVE_PORT="8080")
    def test_serve_port_must_be_int(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_SERVE_PORT must be an integer"):
            get_apcore_settings()

    @override_settings(APCORE_SERVER_NAME="")
    def test_server_name_must_be_non_empty(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_SERVER_NAME must be a non-empty string"):
            get_apcore_settings()

    @override_settings(APCORE_SERVER_NAME="x" * 101)
    def test_server_name_max_length(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_SERVER_NAME must be a non-empty string up to 100 characters"):
            get_apcore_settings()


class TestApcoreSettingsEdgeCases:
    """Test edge cases for settings resolution."""

    @override_settings(APCORE_MODULE_DIR=None)
    def test_none_uses_default(self):
        """Explicit None values should use defaults."""
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.module_dir == "apcore_modules/"

    def test_settings_is_frozen(self):
        """ApcoreSettings should be immutable."""
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        with pytest.raises(AttributeError):
            settings.module_dir = "changed/"  # type: ignore[misc]

    @override_settings(APCORE_SERVE_TRANSPORT="sse")
    def test_sse_transport_accepted(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_transport == "sse"
```

### Step 2: Run tests -- verify they fail

```bash
pytest tests/test_settings.py -x --tb=short
```

Expected: `ImportError: cannot import name 'get_apcore_settings' from 'django_apcore.settings'`

### Step 3: Implement

Create `src/django_apcore/settings.py`:

```python
"""APCORE_* settings resolution and validation.

Reads all APCORE_* settings from django.conf.settings, applies defaults,
validates types and values, and exposes a frozen dataclass for internal use.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Defaults
DEFAULT_MODULE_DIR = "apcore_modules/"
DEFAULT_AUTO_DISCOVER = True
DEFAULT_SERVE_TRANSPORT = "stdio"
DEFAULT_SERVE_HOST = "127.0.0.1"
DEFAULT_SERVE_PORT = 8000
DEFAULT_SERVER_NAME = "apcore-mcp"
DEFAULT_BINDING_PATTERN = "*.binding.yaml"

VALID_TRANSPORTS = ("stdio", "streamable-http", "sse")


@dataclass(frozen=True)
class ApcoreSettings:
    """Validated APCORE_* settings."""

    module_dir: str
    auto_discover: bool
    serve_transport: str
    serve_host: str
    serve_port: int
    server_name: str
    binding_pattern: str


def get_apcore_settings() -> ApcoreSettings:
    """Read and validate all APCORE_* settings from django.conf.settings.

    Returns:
        Validated ApcoreSettings dataclass.

    Raises:
        ImproperlyConfigured: If any setting is invalid.
    """
    # Read with defaults (None means "use default")
    module_dir = getattr(settings, "APCORE_MODULE_DIR", DEFAULT_MODULE_DIR)
    if module_dir is None:
        module_dir = DEFAULT_MODULE_DIR
    if not isinstance(module_dir, (str, Path)):
        raise ImproperlyConfigured(
            f"APCORE_MODULE_DIR must be a string path. Got: {type(module_dir).__name__}"
        )
    module_dir = str(module_dir)

    auto_discover = getattr(settings, "APCORE_AUTO_DISCOVER", DEFAULT_AUTO_DISCOVER)
    if auto_discover is None:
        auto_discover = DEFAULT_AUTO_DISCOVER
    if not isinstance(auto_discover, bool):
        raise ImproperlyConfigured(
            f"APCORE_AUTO_DISCOVER must be a boolean. Got: {type(auto_discover).__name__}"
        )

    serve_transport = getattr(settings, "APCORE_SERVE_TRANSPORT", DEFAULT_SERVE_TRANSPORT)
    if serve_transport is None:
        serve_transport = DEFAULT_SERVE_TRANSPORT
    if serve_transport not in VALID_TRANSPORTS:
        raise ImproperlyConfigured(
            f"APCORE_SERVE_TRANSPORT must be one of: {', '.join(VALID_TRANSPORTS)}. Got: '{serve_transport}'"
        )

    serve_host = getattr(settings, "APCORE_SERVE_HOST", DEFAULT_SERVE_HOST)
    if serve_host is None:
        serve_host = DEFAULT_SERVE_HOST
    if not isinstance(serve_host, str):
        raise ImproperlyConfigured(
            f"APCORE_SERVE_HOST must be a valid hostname or IP. Got: {type(serve_host).__name__}"
        )

    serve_port = getattr(settings, "APCORE_SERVE_PORT", DEFAULT_SERVE_PORT)
    if serve_port is None:
        serve_port = DEFAULT_SERVE_PORT
    if not isinstance(serve_port, int) or isinstance(serve_port, bool):
        raise ImproperlyConfigured(
            f"APCORE_SERVE_PORT must be an integer between 1 and 65535. Got: {type(serve_port).__name__}"
        )
    if not (1 <= serve_port <= 65535):
        raise ImproperlyConfigured(
            f"APCORE_SERVE_PORT must be an integer between 1 and 65535. Got: {serve_port}"
        )

    server_name = getattr(settings, "APCORE_SERVER_NAME", DEFAULT_SERVER_NAME)
    if server_name is None:
        server_name = DEFAULT_SERVER_NAME
    if not isinstance(server_name, str) or len(server_name) == 0 or len(server_name) > 100:
        raise ImproperlyConfigured(
            "APCORE_SERVER_NAME must be a non-empty string up to 100 characters."
        )

    binding_pattern = getattr(settings, "APCORE_BINDING_PATTERN", DEFAULT_BINDING_PATTERN)
    if binding_pattern is None:
        binding_pattern = DEFAULT_BINDING_PATTERN
    if not isinstance(binding_pattern, str):
        raise ImproperlyConfigured(
            "APCORE_BINDING_PATTERN must be a valid glob pattern string."
        )

    return ApcoreSettings(
        module_dir=module_dir,
        auto_discover=auto_discover,
        serve_transport=serve_transport,
        serve_host=serve_host,
        serve_port=serve_port,
        server_name=server_name,
        binding_pattern=binding_pattern,
    )
```

### Step 4: Run tests -- verify they pass

```bash
pytest tests/test_settings.py -x --tb=short -v
```

All tests should pass.

### Step 5: Commit

```bash
git add src/django_apcore/settings.py tests/test_settings.py
git commit -m "feat: ApcoreSettings with validation for all APCORE_* settings"
```

## Acceptance Criteria

- [ ] `get_apcore_settings()` returns a frozen `ApcoreSettings` dataclass
- [ ] All 7 settings (`module_dir`, `auto_discover`, `serve_transport`, `serve_host`, `serve_port`, `server_name`, `binding_pattern`) have correct defaults
- [ ] Invalid types raise `ImproperlyConfigured` with setting name, expected type, and actual type
- [ ] `APCORE_SERVE_TRANSPORT` only accepts `"stdio"`, `"streamable-http"`, `"sse"`
- [ ] `APCORE_SERVE_PORT` only accepts integers in range 1-65535
- [ ] `APCORE_SERVER_NAME` rejects empty strings and strings > 100 characters
- [ ] Explicit `None` values fall back to defaults
- [ ] Settings object is immutable (frozen dataclass)
- [ ] 100% test coverage for `settings.py`

## Dependencies

- **001-setup** -- Requires project structure and `pyproject.toml`

## Estimated Time

3 hours

## Troubleshooting

**Issue: `override_settings` does not seem to affect `get_apcore_settings()`**
If the function caches results, ensure it reads from `django.conf.settings` on every call. The current design intentionally does NOT cache, so `override_settings` works in tests. If you add caching later, provide a `_clear_cache()` test helper.

**Issue: `isinstance(True, int)` returns `True` in Python**
Be aware that Python `bool` is a subclass of `int`. The `APCORE_SERVE_PORT` validation must explicitly reject booleans: `isinstance(value, int) and not isinstance(value, bool)`.

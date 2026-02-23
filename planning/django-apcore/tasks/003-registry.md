# Task 003: Registry Wrapper

## Goal

Implement `get_registry()`, a module-level function that returns a singleton `apcore.Registry` instance for the entire Django process. The registry is created lazily on first access and shared across all components. Provide a `_reset_registry()` test helper for isolation between tests.

## Files Involved

### Create

- `src/django_apcore/registry.py` -- `get_registry()` singleton and `_reset_registry()` helper

### Test

- `tests/test_registry.py` -- Singleton behavior, registry operations, reset helper

## Steps

### Step 1: Write tests (TDD -- Red phase)

Create `tests/test_registry.py`:

```python
# tests/test_registry.py
import pytest


class TestGetRegistry:
    """Test the singleton registry wrapper."""

    def setup_method(self):
        """Reset registry between tests."""
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def test_returns_registry_instance(self):
        """get_registry() returns an apcore.Registry instance."""
        from django_apcore.registry import get_registry

        registry = get_registry()
        # Should be an apcore.Registry (or compatible interface)
        assert registry is not None
        assert hasattr(registry, "register")

    def test_singleton_returns_same_instance(self):
        """Calling get_registry() twice returns the exact same object."""
        from django_apcore.registry import get_registry

        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_reset_creates_new_instance(self):
        """_reset_registry() causes the next call to create a new instance."""
        from django_apcore.registry import _reset_registry, get_registry

        registry1 = get_registry()
        _reset_registry()
        registry2 = get_registry()
        assert registry1 is not registry2

    def test_registry_can_register_module(self):
        """Modules can be registered in the registry."""
        from django_apcore.registry import get_registry

        registry = get_registry()
        # The apcore.Registry should support registration
        # Exact API depends on apcore SDK, but register() should be callable
        assert callable(getattr(registry, "register", None))

    def test_get_registry_is_importable_from_package(self):
        """get_registry should be accessible from django_apcore.registry."""
        from django_apcore.registry import get_registry  # noqa: F401
```

### Step 2: Run tests -- verify they fail

```bash
pytest tests/test_registry.py -x --tb=short
```

Expected: `ImportError: cannot import name 'get_registry' from 'django_apcore.registry'`

### Step 3: Implement

Create `src/django_apcore/registry.py`:

```python
"""Singleton apcore.Registry wrapper for Django.

Provides a process-level singleton Registry that is lazily created on first
access. Thread safety is inherited from apcore.Registry's internal locking.
"""

from __future__ import annotations

import logging

from apcore import Registry

logger = logging.getLogger("django_apcore")

_registry: Registry | None = None


def get_registry() -> Registry:
    """Return the singleton apcore Registry for this Django process.

    The registry is lazily created on first call. It is populated by
    ApcoreAppConfig.ready() auto-discovery if APCORE_AUTO_DISCOVER is True.

    Returns:
        The shared apcore.Registry instance.
    """
    global _registry
    if _registry is None:
        logger.debug("Creating new apcore.Registry instance")
        _registry = Registry()
    return _registry


def _reset_registry() -> None:
    """Reset the singleton registry. For testing only.

    This causes the next call to get_registry() to create a fresh
    Registry instance.
    """
    global _registry
    _registry = None
```

### Step 4: Run tests -- verify they pass

```bash
pytest tests/test_registry.py -x --tb=short -v
```

All tests should pass.

### Step 5: Commit

```bash
git add src/django_apcore/registry.py tests/test_registry.py
git commit -m "feat: singleton get_registry() wrapper for apcore.Registry"
```

## Acceptance Criteria

- [ ] `get_registry()` returns an `apcore.Registry` instance
- [ ] Second call to `get_registry()` returns the exact same object (`is` identity)
- [ ] `_reset_registry()` causes subsequent `get_registry()` to create a new instance
- [ ] The registry supports `register()` method (apcore SDK interface)
- [ ] Logger uses `"django_apcore"` namespace
- [ ] 100% test coverage for `registry.py`

## Dependencies

- **001-setup** -- Requires project structure and `apcore` dependency

## Estimated Time

2 hours

## Troubleshooting

**Issue: `ImportError: No module named 'apcore'`**
The `apcore` SDK must be installed. If not published to PyPI yet, install from local path:
```bash
pip install -e /path/to/apcore-python
```

**Issue: `apcore.Registry` has a different API than expected**
Check the apcore SDK source at `/Users/tercel/WorkSpace/aipartnerup/apcore-python/src/apcore/` to verify the `Registry` class API. The test only checks for `register()` method which is a fundamental part of the Registry interface.

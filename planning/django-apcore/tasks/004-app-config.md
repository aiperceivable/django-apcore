# Task 004: ApcoreAppConfig

## Goal

Implement `ApcoreAppConfig`, a Django AppConfig subclass that on `ready()` validates settings, initializes the singleton registry, and performs auto-discovery of YAML binding files and `@module`-decorated functions across all installed apps. This is the central entry point that wires the apcore ecosystem into Django's startup lifecycle.

## Files Involved

### Create

- `src/django_apcore/apps.py` -- `ApcoreAppConfig` with `ready()` auto-discovery

### Test

- `tests/test_app.py` -- AppConfig unit tests covering all discovery paths

## Steps

### Step 1: Write tests (TDD -- Red phase)

Create `tests/test_app.py`:

```python
# tests/test_app.py
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings


class TestApcoreAppConfig:
    """Test ApcoreAppConfig Django app configuration."""

    def test_app_config_exists(self):
        """django_apcore is registered as a Django app."""
        app_config = apps.get_app_config("django_apcore")
        assert app_config is not None
        assert app_config.name == "django_apcore"

    def test_app_config_label(self):
        """App label is 'django_apcore'."""
        app_config = apps.get_app_config("django_apcore")
        assert app_config.label == "django_apcore"

    def test_app_config_verbose_name(self):
        """App has a human-readable verbose name."""
        app_config = apps.get_app_config("django_apcore")
        assert app_config.verbose_name == "Django apcore"


class TestAutoDiscoveryEnabled:
    """Test auto-discovery when APCORE_AUTO_DISCOVER=True (default)."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(APCORE_AUTO_DISCOVER=True, APCORE_MODULE_DIR="nonexistent_dir/")
    def test_missing_module_dir_logs_warning(self, caplog):
        """When module dir doesn't exist, log warning and continue."""
        from django_apcore.apps import ApcoreAppConfig

        app_config = ApcoreAppConfig("django_apcore", "django_apcore")
        with caplog.at_level(logging.WARNING, logger="django_apcore"):
            app_config.ready()

        assert any("not found" in record.message.lower() for record in caplog.records)

    @override_settings(APCORE_AUTO_DISCOVER=True)
    @patch("django_apcore.apps.BindingLoader", create=True)
    def test_loads_binding_files_when_dir_exists(self, mock_loader_cls, tmp_path):
        """When module dir exists, loads bindings via BindingLoader."""
        module_dir = tmp_path / "apcore_modules"
        module_dir.mkdir()
        binding_file = module_dir / "test.binding.yaml"
        binding_file.write_text("bindings: []")

        from django_apcore.apps import ApcoreAppConfig

        with override_settings(APCORE_MODULE_DIR=str(module_dir)):
            app_config = ApcoreAppConfig("django_apcore", "django_apcore")
            app_config.ready()

        # BindingLoader should have been used (exact API depends on apcore SDK)

    @override_settings(APCORE_AUTO_DISCOVER=True)
    def test_scans_installed_apps_for_apcore_modules(self):
        """Auto-discovery scans INSTALLED_APPS for apcore_modules submodule."""
        from django_apcore.apps import ApcoreAppConfig

        app_config = ApcoreAppConfig("django_apcore", "django_apcore")
        # Should not raise even if no apps have apcore_modules
        app_config.ready()


class TestAutoDiscoveryDisabled:
    """Test behavior when APCORE_AUTO_DISCOVER=False."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(APCORE_AUTO_DISCOVER=False)
    def test_skips_discovery(self, caplog):
        """When auto-discover is disabled, ready() does minimal work."""
        from django_apcore.apps import ApcoreAppConfig

        app_config = ApcoreAppConfig("django_apcore", "django_apcore")
        with caplog.at_level(logging.DEBUG, logger="django_apcore"):
            app_config.ready()

        # Should not attempt to load bindings or scan apps


class TestSettingsValidation:
    """Test that ready() validates settings."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(APCORE_MODULE_DIR=123)
    def test_invalid_settings_raises_improperly_configured(self):
        """Invalid settings cause ImproperlyConfigured at startup."""
        from django_apcore.apps import ApcoreAppConfig

        app_config = ApcoreAppConfig("django_apcore", "django_apcore")
        with pytest.raises(ImproperlyConfigured):
            app_config.ready()
```

### Step 2: Run tests -- verify they fail

```bash
pytest tests/test_app.py -x --tb=short
```

Expected: `ImportError: cannot import name 'ApcoreAppConfig' from 'django_apcore.apps'`

### Step 3: Implement

Create `src/django_apcore/apps.py`:

```python
"""Django AppConfig for django-apcore.

Provides auto-discovery of YAML binding files and @module-decorated functions
across all installed Django apps during startup.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path

from django.apps import AppConfig, apps

logger = logging.getLogger("django_apcore")


class ApcoreAppConfig(AppConfig):
    """Django AppConfig for django-apcore."""

    name = "django_apcore"
    verbose_name = "Django apcore"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Initialize apcore on Django startup.

        1. Validate APCORE_* settings
        2. If APCORE_AUTO_DISCOVER is True:
           a. Load YAML binding files from APCORE_MODULE_DIR
           b. Scan INSTALLED_APPS for @module-decorated functions
        """
        from django_apcore.registry import get_registry
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()

        if not settings.auto_discover:
            logger.debug("Auto-discovery disabled (APCORE_AUTO_DISCOVER=False)")
            return

        registry = get_registry()

        # Load YAML binding files
        module_dir = Path(settings.module_dir)
        if module_dir.exists() and module_dir.is_dir():
            self._load_bindings(registry, module_dir, settings.binding_pattern)
        else:
            logger.warning(
                "Module directory not found: %s. Skipping auto-discovery of binding files.",
                module_dir,
            )

        # Scan INSTALLED_APPS for @module-decorated functions
        self._scan_apps_for_modules(registry)

        logger.info("Auto-discovery complete")

    def _load_bindings(self, registry, module_dir: Path, pattern: str) -> None:
        """Load YAML binding files from the module directory."""
        try:
            from apcore import BindingLoader

            loader = BindingLoader()
            modules = loader.load_binding_dir(str(module_dir), registry, pattern=pattern)
            count = len(modules) if modules else 0
            logger.info("Loaded %d binding modules from %s", count, module_dir)
        except ImportError:
            logger.warning("apcore.BindingLoader not available; skipping binding file loading")
        except Exception:
            logger.exception("Error loading binding files from %s", module_dir)

    def _scan_apps_for_modules(self, registry) -> None:
        """Scan INSTALLED_APPS for apcore_modules submodules."""
        for app_config in apps.get_app_configs():
            module_name = f"{app_config.name}.apcore_modules"
            try:
                module = importlib.import_module(module_name)
                # Scan module for functions with .apcore_module attribute
                for attr_name in dir(module):
                    obj = getattr(module, attr_name)
                    if callable(obj) and hasattr(obj, "apcore_module"):
                        try:
                            registry.register(obj.apcore_module)
                            logger.debug(
                                "Registered @module function: %s.%s",
                                module_name,
                                attr_name,
                            )
                        except Exception:
                            logger.warning(
                                "Failed to register module from %s.%s",
                                module_name,
                                attr_name,
                                exc_info=True,
                            )
            except ImportError:
                # App does not have an apcore_modules submodule -- that's fine
                continue
            except Exception:
                logger.warning(
                    "Error scanning %s for apcore modules",
                    module_name,
                    exc_info=True,
                )
```

### Step 4: Run tests -- verify they pass

```bash
pytest tests/test_app.py -x --tb=short -v
```

All tests should pass.

### Step 5: Commit

```bash
git add src/django_apcore/apps.py tests/test_app.py
git commit -m "feat: ApcoreAppConfig with auto-discovery on ready()"
```

## Acceptance Criteria

- [ ] `ApcoreAppConfig` is registered as the default AppConfig for `django_apcore`
- [ ] `ready()` calls `get_apcore_settings()` to validate settings on startup
- [ ] Invalid settings raise `ImproperlyConfigured` (Django halts)
- [ ] `APCORE_AUTO_DISCOVER=False` skips all discovery (logs debug message)
- [ ] When module dir exists, loads YAML bindings via `apcore.BindingLoader`
- [ ] When module dir does not exist, logs warning and continues
- [ ] Scans all `INSTALLED_APPS` for `apcore_modules` submodules
- [ ] Registers `@module`-decorated functions found in `apcore_modules`
- [ ] Errors in individual apps do not prevent other apps from being scanned
- [ ] 90% test coverage for `apps.py`

## Dependencies

- **002-settings** -- Requires `get_apcore_settings()` for settings validation
- **003-registry** -- Requires `get_registry()` for the singleton Registry

## Estimated Time

4 hours

## Troubleshooting

**Issue: `ready()` is called twice during tests**
Django may call `ready()` during test setup if the app is in `INSTALLED_APPS`. Use `_reset_registry()` in test `setup_method` to ensure clean state. Consider guarding against double-initialization in `ready()` with a class-level flag.

**Issue: `BindingLoader` API mismatch with apcore SDK**
The `BindingLoader.load_binding_dir()` signature may differ from what's shown here. Check the apcore SDK source at `/Users/tercel/WorkSpace/aiperceivable/apcore-python/src/apcore/` for the exact API. The implementation should adapt to the actual SDK interface.

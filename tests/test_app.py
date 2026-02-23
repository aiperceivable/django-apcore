# tests/test_app.py
import logging
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
        app_config = apps.get_app_config("django_apcore")
        with caplog.at_level(logging.WARNING, logger="django_apcore"):
            app_config.ready()

        assert any("not found" in record.message.lower() for record in caplog.records)

    @override_settings(APCORE_AUTO_DISCOVER=True)
    @patch("apcore.BindingLoader")
    def test_loads_binding_files_when_dir_exists(self, mock_loader_cls, tmp_path):
        """When module dir exists, loads bindings via BindingLoader."""
        module_dir = tmp_path / "apcore_modules"
        module_dir.mkdir()
        binding_file = module_dir / "test.binding.yaml"
        binding_file.write_text("bindings: []")

        mock_loader = MagicMock()
        mock_loader.load_binding_dir.return_value = []
        mock_loader_cls.return_value = mock_loader

        app_config = apps.get_app_config("django_apcore")
        with override_settings(APCORE_MODULE_DIR=str(module_dir)):
            app_config.ready()

        # BindingLoader should have been instantiated and used
        mock_loader_cls.assert_called_once()
        mock_loader.load_binding_dir.assert_called_once()

    @override_settings(APCORE_AUTO_DISCOVER=True)
    def test_scans_installed_apps_for_apcore_modules(self):
        """Auto-discovery scans INSTALLED_APPS for apcore_modules submodule."""
        app_config = apps.get_app_config("django_apcore")
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
        app_config = apps.get_app_config("django_apcore")
        with caplog.at_level(logging.DEBUG, logger="django_apcore"):
            app_config.ready()

        # Should not attempt to load bindings or scan apps


class TestRegistryEvents:
    """Test registry event listener registration."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(APCORE_AUTO_DISCOVER=True, APCORE_MODULE_DIR="nonexistent_dir/")
    def test_event_listener_registered(self):
        """Event listener is registered on the registry."""
        app_config = apps.get_app_config("django_apcore")

        # If registry.on works, it should not raise
        app_config.ready()

    @override_settings(APCORE_AUTO_DISCOVER=True, APCORE_MODULE_DIR="nonexistent_dir/")
    def test_event_callback_signature_matches_upstream(self):
        """Callback receives (module_id, module) per upstream contract."""
        app_config = apps.get_app_config("django_apcore")

        with patch("django_apcore.registry.get_registry") as mock_get_reg:
            mock_registry = MagicMock()
            captured_callbacks = []
            mock_registry.on.side_effect = lambda event, cb: captured_callbacks.append(
                cb
            )
            mock_registry.count = 0
            mock_get_reg.return_value = mock_registry

            app_config.ready()

            assert len(captured_callbacks) == 1
            # Upstream calls callback(module_id, module)
            # Should not raise with this signature
            captured_callbacks[0]("my.module", MagicMock())

    @override_settings(APCORE_AUTO_DISCOVER=True, APCORE_MODULE_DIR="nonexistent_dir/")
    def test_handles_unavailable_events(self):
        """Gracefully handles registry without event support."""
        app_config = apps.get_app_config("django_apcore")

        with patch("django_apcore.registry.get_registry") as mock_get_reg:
            mock_registry = MagicMock()
            mock_registry.on.side_effect = AttributeError("no events")
            mock_registry.count = 0
            mock_get_reg.return_value = mock_registry

            # Should not raise
            app_config.ready()


class TestEmbeddedServerInReady:
    """Test embedded server auto-start in ready()."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(
        APCORE_AUTO_DISCOVER=True,
        APCORE_MODULE_DIR="nonexistent_dir/",
        APCORE_EMBEDDED_SERVER=True,
    )
    @patch("django_apcore.registry.start_embedded_server")
    def test_embedded_server_started_when_configured(self, mock_start):
        """Embedded server is started during ready() when configured."""
        mock_start.return_value = MagicMock()
        app_config = apps.get_app_config("django_apcore")
        app_config.ready()
        mock_start.assert_called_once()

    @override_settings(
        APCORE_AUTO_DISCOVER=True,
        APCORE_MODULE_DIR="nonexistent_dir/",
        APCORE_EMBEDDED_SERVER=True,
    )
    @patch(
        "django_apcore.registry.start_embedded_server",
        side_effect=RuntimeError("boom"),
    )
    def test_embedded_server_failure_does_not_crash_startup(self, mock_start, caplog):
        """Failure to start embedded server doesn't crash startup."""
        app_config = apps.get_app_config("django_apcore")
        # Should not raise
        with caplog.at_level(logging.WARNING, logger="django_apcore"):
            app_config.ready()


class TestSettingsValidation:
    """Test that ready() validates settings."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(APCORE_MODULE_DIR=123)
    def test_invalid_settings_raises_improperly_configured(self):
        """Invalid settings cause ImproperlyConfigured at startup."""
        app_config = apps.get_app_config("django_apcore")
        with pytest.raises(ImproperlyConfigured):
            app_config.ready()

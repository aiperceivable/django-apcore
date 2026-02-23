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

    @override_settings(APCORE_AUTO_DISCOVER=True)
    def test_discover_is_called(self):
        """When auto-discover is enabled, registry.discover() is called."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            mock_get_reg.return_value = mock_registry

            app_config = apps.get_app_config("django_apcore")
            app_config.ready()

            mock_registry.discover.assert_called_once()

    @override_settings(APCORE_AUTO_DISCOVER=True)
    def test_ready_completes_without_error(self):
        """Auto-discovery completes without error even with no modules."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            mock_get_reg.return_value = mock_registry

            app_config = apps.get_app_config("django_apcore")
            # Should not raise
            app_config.ready()

    @override_settings(APCORE_AUTO_DISCOVER=True)
    def test_discover_count_logged(self, caplog):
        """Auto-discovery logs the count of discovered modules."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 3
            mock_get_reg.return_value = mock_registry

            app_config = apps.get_app_config("django_apcore")
            with caplog.at_level(logging.INFO, logger="django_apcore"):
                app_config.ready()

            assert any(
                "3 modules registered" in record.message
                for record in caplog.records
            )


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

    @override_settings(APCORE_AUTO_DISCOVER=True)
    def test_event_listener_registered(self):
        """Event listener is registered on the registry."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            mock_get_reg.return_value = mock_registry

            app_config = apps.get_app_config("django_apcore")
            # If registry.on works, it should not raise
            app_config.ready()

            mock_registry.on.assert_called_once()

    @override_settings(APCORE_AUTO_DISCOVER=True)
    def test_event_callback_signature_matches_upstream(self):
        """Callback receives (module_id, module) per upstream contract."""
        app_config = apps.get_app_config("django_apcore")

        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            captured_callbacks = []
            mock_registry.on.side_effect = lambda event, cb: captured_callbacks.append(
                cb
            )
            mock_get_reg.return_value = mock_registry

            app_config.ready()

            assert len(captured_callbacks) == 1
            # Upstream calls callback(module_id, module)
            # Should not raise with this signature
            captured_callbacks[0]("my.module", MagicMock())

    @override_settings(APCORE_AUTO_DISCOVER=True)
    def test_handles_unavailable_events(self):
        """Gracefully handles registry without event support."""
        app_config = apps.get_app_config("django_apcore")

        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.on.side_effect = AttributeError("no events")
            mock_registry.discover.return_value = 0
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
        APCORE_EMBEDDED_SERVER=True,
    )
    @patch("django_apcore.registry.start_embedded_server")
    def test_embedded_server_started_when_configured(self, mock_start):
        """Embedded server is started during ready() when configured."""
        mock_start.return_value = MagicMock()
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            mock_get_reg.return_value = mock_registry

            app_config = apps.get_app_config("django_apcore")
            app_config.ready()

        mock_start.assert_called_once()

    @override_settings(
        APCORE_AUTO_DISCOVER=True,
        APCORE_EMBEDDED_SERVER=True,
    )
    @patch(
        "django_apcore.registry.start_embedded_server",
        side_effect=RuntimeError("boom"),
    )
    def test_embedded_server_failure_does_not_crash_startup(self, mock_start, caplog):
        """Failure to start embedded server doesn't crash startup."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            mock_get_reg.return_value = mock_registry

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


class TestExtensionFirstStartup:
    """Test Extension-First startup flow."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(APCORE_AUTO_DISCOVER=True)
    def test_ready_triggers_discover(self):
        """ready() calls registry.discover() for auto-discovery."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            mock_get_reg.return_value = mock_registry

            app_config = apps.get_app_config("django_apcore")
            app_config.ready()

            mock_registry.discover.assert_called_once()

    @override_settings(APCORE_AUTO_DISCOVER=True, APCORE_HOT_RELOAD=True)
    def test_ready_enables_hot_reload(self):
        """ready() calls registry.watch() when hot_reload is enabled."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            mock_get_reg.return_value = mock_registry

            app_config = apps.get_app_config("django_apcore")
            app_config.ready()

            mock_registry.watch.assert_called_once()

    @override_settings(APCORE_AUTO_DISCOVER=True)
    def test_ready_calls_get_executor(self):
        """ready() calls get_executor() to trigger ExtensionManager assembly."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor") as mock_get_exec,
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            mock_get_reg.return_value = mock_registry

            app_config = apps.get_app_config("django_apcore")
            app_config.ready()

            mock_get_exec.assert_called_once()

    @override_settings(APCORE_AUTO_DISCOVER=True, APCORE_HOT_RELOAD=True)
    def test_hot_reload_import_error_handled(self, caplog):
        """ImportError from registry.watch() is handled gracefully."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            mock_registry.watch.side_effect = ImportError("no watchdog")
            mock_get_reg.return_value = mock_registry

            app_config = apps.get_app_config("django_apcore")
            with caplog.at_level(logging.WARNING, logger="django_apcore"):
                app_config.ready()

            assert any("watchdog" in record.message for record in caplog.records)

    @override_settings(APCORE_AUTO_DISCOVER=True, APCORE_HOT_RELOAD=True)
    def test_hot_reload_general_error_handled(self, caplog):
        """General exception from registry.watch() is handled gracefully."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            mock_registry.watch.side_effect = RuntimeError("boom")
            mock_get_reg.return_value = mock_registry

            app_config = apps.get_app_config("django_apcore")
            with caplog.at_level(logging.WARNING, logger="django_apcore"):
                app_config.ready()

            assert any(
                "hot-reload" in record.message.lower() for record in caplog.records
            )

    @override_settings(APCORE_AUTO_DISCOVER=False)
    def test_auto_discover_false_skips_everything(self, caplog):
        """When auto_discover is False, no discovery or executor setup occurs."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor") as mock_get_exec,
        ):
            app_config = apps.get_app_config("django_apcore")
            with caplog.at_level(logging.DEBUG, logger="django_apcore"):
                app_config.ready()

            mock_get_reg.assert_not_called()
            mock_get_exec.assert_not_called()

    @override_settings(APCORE_AUTO_DISCOVER=True, APCORE_HOT_RELOAD=False)
    def test_hot_reload_not_called_when_disabled(self):
        """registry.watch() is NOT called when hot_reload is False."""
        with (
            patch("django_apcore.registry.get_registry") as mock_get_reg,
            patch("django_apcore.registry.get_executor"),
        ):
            mock_registry = MagicMock()
            mock_registry.discover.return_value = 0
            mock_get_reg.return_value = mock_registry

            app_config = apps.get_app_config("django_apcore")
            app_config.ready()

            mock_registry.watch.assert_not_called()

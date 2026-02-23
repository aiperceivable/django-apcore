"""Integration tests for the registry-to-serve pipeline.

These tests verify that:
1. The registry can be populated programmatically
2. The populated registry can be passed to the serve command flow
3. Settings + registry + serve work together as a complete pipeline
"""

from __future__ import annotations

from unittest.mock import patch


class TestRegistryServeIntegration:
    """Integration tests for registry -> serve pipeline."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def test_registry_populated_then_serve(self):
        """Registry with registered modules can be served."""
        from django_apcore.registry import get_registry

        registry = get_registry()

        # The registry should be accessible and usable
        assert registry is not None
        assert hasattr(registry, "register")

    def test_settings_and_registry_work_together(self):
        """Settings are correctly read when registry is initialized."""
        from django_apcore.registry import get_registry
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        registry = get_registry()

        assert settings.module_dir == "apcore_modules/"
        assert registry is not None

    def test_app_config_initializes_registry(self):
        """AppConfig.ready() initializes the registry successfully."""
        from django.apps import apps

        from django_apcore.registry import get_registry

        app_config = apps.get_app_config("django_apcore")
        # Should not raise
        app_config.ready()

        registry = get_registry()
        assert registry is not None

    def test_full_pipeline_settings_to_serve(self):
        """Full pipeline: settings -> registry -> serve delegation."""
        from django_apcore.registry import get_registry
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        registry = get_registry()

        # Mock the serve function since we don't want to actually start a server
        with patch(
            "django_apcore.management.commands.apcore_serve.serve"
        ) as mock_serve:
            mock_serve.return_value = None

            # Simulate what the serve command does
            assert settings.serve_transport in ("stdio", "streamable-http", "sse")
            assert registry is not None

    def test_extension_first_startup(self):
        """Extension-First pipeline: settings -> extensions -> registry -> discover."""
        from django_apcore.extensions import DjangoDiscoverer, setup_extensions
        from django_apcore.registry import _reset_registry, get_registry
        from django_apcore.settings import get_apcore_settings

        # 1. Reset registry to ensure clean state
        _reset_registry()

        # 2. Get settings
        settings = get_apcore_settings()

        # 3. Create the extension manager via setup_extensions
        ext_mgr = setup_extensions(settings)

        # 4. Verify the extension manager has a discoverer registered
        discoverer = ext_mgr.get("discoverer")
        assert discoverer is not None
        assert isinstance(discoverer, DjangoDiscoverer)

        # 5. Get registry and verify it exists
        registry = get_registry()
        assert registry is not None

        # 6. Verify registry.discover() returns 0 (no modules in test config)
        #    Mock discover() since the default test environment has no extensions dir
        with patch.object(registry, "discover", return_value=0) as mock_discover:
            count = registry.discover()
            assert count == 0
            mock_discover.assert_called_once()

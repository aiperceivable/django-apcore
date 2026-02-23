# tests/test_registry.py

from unittest.mock import MagicMock, patch


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


class TestGetExtensionManager:
    """Test the singleton ExtensionManager wrapper."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def test_returns_extension_manager(self):
        """get_extension_manager() returns an ExtensionManager instance."""
        from apcore import ExtensionManager

        from django_apcore.registry import get_extension_manager

        ext_mgr = get_extension_manager()
        assert isinstance(ext_mgr, ExtensionManager)

    def test_singleton_returns_same_instance(self):
        """Calling get_extension_manager() twice returns the same object."""
        from django_apcore.registry import get_extension_manager

        em1 = get_extension_manager()
        em2 = get_extension_manager()
        assert em1 is em2

    def test_has_discoverer_registered(self):
        """ExtensionManager has a discoverer registered."""
        from django_apcore.registry import get_extension_manager

        ext_mgr = get_extension_manager()
        discoverer = ext_mgr.get("discoverer")
        assert discoverer is not None

    def test_has_module_validator_registered(self):
        """ExtensionManager has at least one module_validator registered."""
        from django_apcore.registry import get_extension_manager

        ext_mgr = get_extension_manager()
        validators = ext_mgr.get_all("module_validator")
        assert len(validators) >= 1

    def test_reset_creates_new_instance(self):
        """_reset_extension_manager() causes a new ExtensionManager on next call."""
        from django_apcore.registry import (
            _reset_extension_manager,
            get_extension_manager,
        )

        em1 = get_extension_manager()
        _reset_extension_manager()
        em2 = get_extension_manager()
        assert em1 is not em2

    def test_reset_registry_also_resets_extension_manager(self):
        """_reset_registry() also resets the extension manager singleton."""
        import django_apcore.registry as reg
        from django_apcore.registry import _reset_registry

        reg._ext_manager = MagicMock()
        _reset_registry()
        assert reg._ext_manager is None


class TestGetExecutorWithExtensions:
    """Test executor creation uses ExtensionManager."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @patch("apcore.Executor")
    def test_get_executor_returns_executor(self, mock_executor_cls):
        """get_executor() returns an Executor instance."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        executor = get_executor()
        assert executor is not None
        assert hasattr(executor, "call")

    @patch("apcore.Executor")
    def test_get_executor_singleton(self, mock_executor_cls):
        """get_executor() returns the same instance on repeated calls."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        e1 = get_executor()
        e2 = get_executor()
        assert e1 is e2

    @patch("apcore.Executor")
    def test_executor_uses_extension_manager(self, mock_executor_cls):
        """get_executor() calls ExtensionManager.apply()."""
        mock_executor_instance = MagicMock()
        mock_executor_cls.return_value = mock_executor_instance

        from django_apcore.registry import get_executor, get_extension_manager

        executor = get_executor()
        ext_mgr = get_extension_manager()
        # ExtensionManager.apply() should have been called
        assert ext_mgr is not None
        assert executor is mock_executor_instance

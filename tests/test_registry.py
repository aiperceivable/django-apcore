# tests/test_registry.py


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

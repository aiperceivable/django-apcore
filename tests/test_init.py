# tests/test_init.py


def test_package_version_exists():
    """django_apcore exposes a __version__ string."""
    import django_apcore

    assert hasattr(django_apcore, "__version__")
    assert isinstance(django_apcore.__version__, str)
    assert len(django_apcore.__version__) > 0


def test_version():
    import django_apcore

    assert django_apcore.__version__ == "0.1.0"


def test_package_importable():
    """django_apcore can be imported without errors."""
    import django_apcore  # noqa: F401

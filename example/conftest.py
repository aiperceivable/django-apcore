"""pytest-django configuration for the demo project's functional tests.

Only activates when pytest is run from the example/ directory.
When run from the project root, this conftest is a no-op.
"""

from __future__ import annotations

from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent


def pytest_configure(config: object) -> None:
    rootdir = Path(str(getattr(config, "rootdir", "")))
    if rootdir != _THIS_DIR:
        return

    import sys

    sys.path.insert(0, str(_THIS_DIR))

    from django.conf import settings

    if settings.configured:
        return

    import django

    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django_apcore",
            "demo",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        ROOT_URLCONF="demo.urls",
        SECRET_KEY="test-secret",
        APCORE_SERVER_NAME="task-manager-mcp",
    )
    django.setup()

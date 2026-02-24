"""pytest-django configuration for the demo project's functional tests."""

import sys
from pathlib import Path

# Make demo package importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

import django
from django.conf import settings


def pytest_configure():
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
    )
    django.setup()

"""Minimal Django settings for the django-apcore ACL demo.

Run from the repo root:

    python examples/acl_demo/manage.py runserver
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "demo-not-a-secret"  # noqa: S105 — demo only
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_apcore",
]

# Minimal middleware: no CSRF / session / auth middleware, so this demo API
# accepts DELETE without a CSRF token. Authentication is faked from the
# `X-Roles` header in the views — do NOT do this in production.
MIDDLEWARE: list[str] = []

ROOT_URLCONF = "examples.acl_demo.urls"

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Point apcore at this demo's ACL. django-apcore loads it and applies it to the
# Executor (executor.set_acl) on first use.
APCORE_ACL_PATH = str(BASE_DIR / "acl.yaml")

"""Django settings for the apcore demo project."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "demo-secret-key-not-for-production"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_apcore",
    "demo",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "demo.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# apcore settings
APCORE_SERVE_TRANSPORT = "streamable-http"
APCORE_SERVE_HOST = "0.0.0.0"
APCORE_SERVE_PORT = 9090
APCORE_SERVER_NAME = "demo-mcp"

# Explorer: dev/staging only. Exposes module schemas and execution via HTTP.
# Do NOT enable in production — there is no auth on these endpoints.
APCORE_EXPLORER_ENABLED = True  # browse modules at /apcore/
APCORE_EXPLORER_ALLOW_EXECUTE = True  # allow Try-it execution (calls Executor)

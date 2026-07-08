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

# ---------------------------------------------------------------------------
# apcore settings
# ---------------------------------------------------------------------------

APCORE_MODULE_DIR = str(BASE_DIR / "demo" / "apcore_modules")
APCORE_SERVE_TRANSPORT = "streamable-http"
APCORE_SERVE_HOST = "0.0.0.0"
APCORE_SERVE_PORT = 9090
APCORE_SERVER_NAME = "task-manager-mcp"
APCORE_SERVE_VALIDATE_INPUTS = True

# Explorer: dev/staging only. Exposes tool schemas and execution via HTTP.
# Do NOT enable in production — there is no auth on these endpoints.
# Served by the MCP server (apcore-mcp) on the MCP port, not the Django port.
APCORE_EXPLORER_ENABLED = True  # browse tools at /explorer on MCP server
APCORE_EXPLORER_ALLOW_EXECUTE = True  # allow Try-it execution

# Output formatter (apcore-mcp 0.10.0+)
# Set to "apcore_toolkit.to_markdown" for Markdown-formatted results.
# Default: None (raw JSON)
# APCORE_OUTPUT_FORMATTER = "apcore_toolkit.to_markdown"

# AI Enhancement (apcore-toolkit 0.2.0+)
# Enable to auto-enhance scanned modules via local SLM.
# Requires APCORE_AI_ENABLED=true env var and a running Ollama/vLLM instance.
# APCORE_AI_ENHANCE = True

# JWT Authentication (apcore-mcp >= 0.7.0)
# Uncomment to enable JWT auth on the MCP server.
# Clients must send "Authorization: Bearer <token>" header.
# APCORE_JWT_SECRET = "change-me-in-production"
# APCORE_JWT_ALGORITHM = "HS256"
# APCORE_JWT_AUDIENCE = "task-manager-api"
# APCORE_JWT_ISSUER = "task-manager"

# Observability
APCORE_TRACING_ENABLED = True
APCORE_TRACING_EXPORTER = "stdout"
APCORE_METRICS_ENABLED = True
APCORE_LOGGING_ENABLED = True
APCORE_LOGGING_FORMAT = "json"

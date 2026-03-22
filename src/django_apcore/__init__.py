"""django-apcore: Django integration for apcore.

Scan existing REST APIs and serve them as MCP tools for AI agents.

Usage::

    from django_apcore import DjangoApcore

    app = DjangoApcore()
    result = app.call("users.list", {"page": 1}, request=request)
"""

from django_apcore.client import DjangoApcore
from importlib.metadata import version as _get_version

try:
    __version__ = _get_version("django-apcore")
except Exception:
    __version__ = "unknown"

__all__ = ["DjangoApcore", "__version__"]

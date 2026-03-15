"""django-apcore: Django integration for apcore.

Scan existing REST APIs and serve them as MCP tools for AI agents.

Usage::

    from django_apcore import DjangoApcore

    app = DjangoApcore()
    result = app.call("users.list", {"page": 1}, request=request)
"""

from django_apcore.client import DjangoApcore

__version__ = "0.3.0"

__all__ = ["DjangoApcore", "__version__"]

"""URL configuration for the django-apcore explorer.

Usage in your project's urls.py::

    from django.urls import include, path
    from django_apcore.urls import explorer_urlpatterns

    urlpatterns = [
        path("apcore/", include(explorer_urlpatterns)),
        # ... your other URLs
    ]

Or let django-apcore auto-include via AppConfig when
APCORE_EXPLORER_ENABLED=True (recommended).
"""

from __future__ import annotations

from django.urls import path

from django_apcore.web.api import call_module, get_module, list_modules
from django_apcore.web.views import explorer_page

app_name = "apcore_explorer"

explorer_urlpatterns = [
    path("", explorer_page, name="explorer"),
    path("modules/", list_modules, name="list-modules"),
    path("modules/<path:module_id>/call/", call_module, name="call-module"),
    path("modules/<path:module_id>/", get_module, name="module-detail"),
]

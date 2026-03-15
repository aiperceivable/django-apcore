"""Django views provided by django-apcore.

Provides an explorer redirect view that guides developers from the Django
server to the MCP server's Tool Explorer UI.
"""

from __future__ import annotations

from django.http import HttpResponse


def explorer_redirect(request: object) -> HttpResponse:
    """Redirect to the MCP server's Tool Explorer UI.

    When developers visit ``/explorer/`` on the Django port, this view
    returns a helpful page with a link to the correct MCP server URL.

    Usage in ``urls.py``::

        from django_apcore.views import explorer_redirect

        urlpatterns = [
            path("explorer/", explorer_redirect),
            # ...
        ]
    """
    from django_apcore.settings import get_apcore_settings

    settings = get_apcore_settings()

    if not settings.explorer_enabled:
        return HttpResponse(
            "<h2>Tool Explorer is disabled</h2>"
            "<p>Set <code>APCORE_EXPLORER_ENABLED = True</code> in your "
            "Django settings to enable it.</p>",
            content_type="text/html",
            status=404,
        )

    host = settings.serve_host
    port = settings.serve_port
    prefix = settings.explorer_prefix

    # Use localhost for display if bound to 0.0.0.0
    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    url = f"http://{display_host}:{port}{prefix}/"

    return HttpResponse(
        f"<h2>Tool Explorer</h2>"
        f"<p>The Tool Explorer runs on the <strong>MCP server</strong>, "
        f"not the Django server.</p>"
        f'<p><a href="{url}">{url}</a></p>'
        f"<p>Start the MCP server with:</p>"
        f"<pre>python manage.py apcore_serve --transport streamable-http "
        f"--explorer</pre>"
        f'<script>window.location.href = "{url}";</script>',
        content_type="text/html",
    )

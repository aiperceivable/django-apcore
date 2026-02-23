"""Django Context/Identity adapter for apcore.

Provides DjangoContextFactory that creates apcore Context objects from
Django HTTP requests, mapping request.user to Identity.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("django_apcore")


class DjangoContextFactory:
    """Creates apcore Context from Django HTTP requests.

    Implements the apcore ContextFactory protocol:
        create_context(request) -> Context
    """

    def create_context(self, request: Any) -> Any:
        """Create an apcore Context from a Django request.

        Args:
            request: Django HttpRequest (or any object with optional .user).

        Returns:
            apcore Context with Identity derived from request.user.
        """
        from apcore import Context

        identity = self._extract_identity(request)
        return Context.create(identity=identity)

    def _extract_identity(self, request: Any) -> Any:
        """Extract an apcore Identity from a Django request.

        Args:
            request: Django HttpRequest.

        Returns:
            apcore Identity with user info, or anonymous identity.
        """
        from apcore import Identity

        user = getattr(request, "user", None)

        if user is None or not getattr(user, "is_authenticated", False):
            return Identity(
                id="anonymous",
                type="anonymous",
            )

        # Extract group names safely
        try:
            groups = list(user.groups.values_list("name", flat=True))
        except Exception:
            groups = []

        attrs: dict[str, Any] = {}
        if hasattr(user, "is_staff"):
            attrs["is_staff"] = user.is_staff
        if hasattr(user, "is_superuser"):
            attrs["is_superuser"] = user.is_superuser

        return Identity(
            id=str(user.pk),
            type="user",
            roles=groups,
            attrs=attrs,
        )

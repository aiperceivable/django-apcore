"""Views + apcore modules for the django-apcore ACL demo.

Each view calls an apcore module via ``apcore.call(id, inputs, request=request)``.
``DjangoContextFactory`` turns ``request.user`` into an apcore ``Identity(roles=...)``,
and the Executor enforces ``acl.yaml`` before the module runs. A denied call raises
``ACLDeniedError``, which the view maps to HTTP 403.
"""

from __future__ import annotations

import contextlib
from types import SimpleNamespace

from apcore import ACLDeniedError
from django.http import HttpRequest, JsonResponse

from django_apcore import DjangoApcore

apcore = DjangoApcore()


def register_modules() -> None:
    """(Re-)register the demo's ACL-protected apcore modules.

    Idempotent (unregisters first), so it is safe to call at import — for the
    running server — and again from tests, which share the process-wide registry
    with the rest of the suite.

    Two modules, protected by ``acl.yaml``:
      * ``orders.delete`` -> admins only
      * ``orders.list``   -> public (read)
    """
    for module_id in ("orders.delete", "orders.list"):
        with contextlib.suppress(Exception):
            apcore.registry.unregister(module_id)

    @apcore.module(id="orders.delete")
    def delete_order(order_id: int) -> dict:
        return {"deleted": order_id}

    @apcore.module(id="orders.list")
    def list_orders() -> dict:
        return {"orders": [{"id": 1}, {"id": 2}]}


register_modules()


class _FakeGroups:
    """Stand-in for Django's ``user.groups`` related manager. DjangoContextFactory
    reads roles via ``user.groups.values_list("name", flat=True)``."""

    def __init__(self, names) -> None:
        self._names = list(names)

    def values_list(self, field: str, flat: bool = False):
        return list(self._names)


def _apply_fake_auth(request: HttpRequest) -> None:
    """Demo shortcut for authentication: read comma-separated roles from the
    ``X-Roles`` header and attach a fake user. Real apps resolve the user from a
    Django session / JWT; apcore only needs ``is_authenticated`` + ``groups``."""
    roles = request.headers.get("X-Roles")
    if roles:
        # DjangoContextFactory reads ``user.pk`` (id), ``user.is_authenticated``
        # and ``user.groups.values_list("name", ...)`` (roles).
        request.user = SimpleNamespace(  # type: ignore[assignment] — demo fake user
            pk="u1",
            is_authenticated=True,
            groups=_FakeGroups(r.strip() for r in roles.split(",") if r.strip()),
        )
    # No header -> no authenticated user -> DjangoContextFactory yields anonymous.


def delete_order_view(request: HttpRequest, order_id: int) -> JsonResponse:
    _apply_fake_auth(request)
    try:
        result = apcore.call("orders.delete", {"order_id": order_id}, request=request)
        return JsonResponse(result)
    except ACLDeniedError as exc:
        return JsonResponse({"detail": str(exc)}, status=403)


def list_orders_view(request: HttpRequest) -> JsonResponse:
    _apply_fake_auth(request)
    try:
        result = apcore.call("orders.list", {}, request=request)
        return JsonResponse(result)
    except ACLDeniedError as exc:
        return JsonResponse({"detail": str(exc)}, status=403)

"""End-to-end tests for the django-apcore ACL demo (examples/acl_demo).

Runs under the suite's ``tests.settings`` (not the demo's own settings), so the
demo's ``acl.yaml`` is loaded onto the executor explicitly and the views are
driven with ``RequestFactory`` rather than a live server.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from apcore import ACL
from django.test import RequestFactory

# Importing the demo views registers its apcore modules into the singleton registry.
from examples.acl_demo import views


@pytest.fixture(autouse=True)
def _demo_state():
    # The suite shares one process-wide registry/executor; re-establish the demo's
    # modules and ACL before each test so ordering with other tests doesn't matter.
    views.register_modules()
    acl_path = Path(views.__file__).parent / "acl.yaml"
    views.apcore.executor.set_acl(ACL.load(str(acl_path)))


def _delete(roles: str | None = None):
    extra = {"HTTP_X_ROLES": roles} if roles else {}
    request = RequestFactory().delete("/orders/1", **extra)
    return views.delete_order_view(request, order_id=1)


def test_delete_anonymous_is_denied():
    assert _delete(roles=None).status_code == 403


def test_delete_non_admin_is_denied():
    assert _delete(roles="user").status_code == 403


def test_delete_admin_is_allowed():
    resp = _delete(roles="admin")
    assert resp.status_code == 200
    assert json.loads(resp.content) == {"deleted": 1}


def test_list_is_public():
    resp = views.list_orders_view(RequestFactory().get("/orders"))
    assert resp.status_code == 200
    assert json.loads(resp.content) == {"orders": [{"id": 1}, {"id": 2}]}

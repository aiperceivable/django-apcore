# Django + apcore ACL demo

Shows how a Django application enforces **apcore Access Control Lists (ACL)**
on apcore module calls made from within request handlers.

## What it demonstrates

- Loading an ACL from YAML via `APCORE_ACL_PATH` (a Django setting here).
- Mapping a Django request's authenticated user (`request.user`) to an apcore
  `Identity(roles=...)` through `DjangoContextFactory` — roles come from the
  user's group names.
- Role-based `allow`/`deny` enforced by the Executor before a module runs, with
  denied calls surfacing as `ACLDeniedError` → HTTP 403.

## Files

| File | Purpose |
|------|---------|
| `settings.py` | Minimal Django settings; sets `APCORE_ACL_PATH` and an empty middleware stack (so the demo API accepts `DELETE` without CSRF). |
| `acl.yaml` | ACL rules: admins may call anything; `orders.list` is public; everything else is denied by `default_effect: deny`. |
| `views.py` | Two ACL-protected apcore modules (`orders.delete`, `orders.list`), the views that call them, and a demo `X-Roles` auth shortcut. |
| `urls.py` | Routes `GET /orders` and `DELETE /orders/<id>` to the views. |
| `manage.py` | Runs the demo. |

## Run it

```bash
# From the repo root.
python examples/acl_demo/manage.py runserver
```

```bash
curl -X DELETE 127.0.0.1:8000/orders/1                     # 403  (anonymous)
curl -X DELETE 127.0.0.1:8000/orders/1 -H 'X-Roles: user'  # 403  (authenticated, not admin)
curl -X DELETE 127.0.0.1:8000/orders/1 -H 'X-Roles: admin' # 200  {"deleted": 1}
curl 127.0.0.1:8000/orders                                 # 200  (read is public)
```

> Use `127.0.0.1`, not `localhost`. On macOS `localhost` resolves to IPv6 `::1`
> first, while Django's dev server binds IPv4 `127.0.0.1` by default — so
> `curl localhost:8000` can silently hit a *different* server holding IPv6 port
> 8000. `127.0.0.1` forces IPv4. (Or run on another port: `runserver 127.0.0.1:8001`.)

> The `X-Roles` header is a demo shortcut standing in for real authentication.
> In production, resolve the user from Django's session/JWT auth (so
> `request.user` is a real `User` with `groups`) — apcore reads
> `is_authenticated` and the user's group names as roles.

## How the pieces connect

```
HTTP request
  └─ view attaches request.user (id, groups) — real auth in production
       └─ view calls apcore.call(module_id, inputs, request=request)
            └─ DjangoContextFactory → Identity(roles = user's group names)
                 └─ Executor checks ACL (first-match-wins on callers/targets/conditions.roles)
                      ├─ allow → module runs
                      └─ deny  → ACLDeniedError → HTTP 403
```

ACL guards **apcore module calls** (the Executor), not raw Django views — so the
same rules apply whether a module is invoked from a Django view (as here), from
an MCP client via `apcore_serve`, or from the generated CLI (`create_cli`).

## ACL rule format

```yaml
default_effect: deny          # fallback when no rule matches
rules:
  - description: Admins may call any module
    callers: ["*"]            # caller-id glob patterns
    targets: ["*"]            # module-id glob patterns
    effect: allow             # allow | deny
    conditions:               # optional: roles | identity_types | max_call_depth
      roles: ["admin"]
```

See `src/django_apcore/context.py` for how `request.user` is mapped to the
`Identity` that `conditions.roles` matches against.

## Test

The end-to-end behavior is covered by `tests/test_acl_demo.py`.

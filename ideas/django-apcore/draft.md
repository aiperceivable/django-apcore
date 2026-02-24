# django-apcore

> Status: Ready | Draft v4 | 2026-02-19

## One-Liner
Django's apcore integration -- zero-intrusion, 3 steps to turn any existing Django project into an MCP Server.

## Problem
Django's MCP ecosystem is severely fragmented (8+ packages, no dominant player), and all existing solutions are merely MCP transport layers, lacking protocol-level module definition standards. fastapi-mcp's downloads are 82x the sum of all Django MCP packages combined, putting pressure on Django developers to migrate to FastAPI.

## Target Users
Three user segments, served in layers:

| User Type | Share of Django Community | Entry Point | Extra Dependencies |
|---------|---------------|---------|---------|
| New code / ML teams | ~8-10% | `@module` decorator | None |
| DRF API users | ~49% | `manage.py apcore_scan --source drf` | drf-spectacular |
| django-ninja users | ~10% (+67% YoY) | `manage.py apcore_scan --source ninja` | django-ninja |

## Core Experience (Zero-Intrusion, 3 Steps)

### Existing Projects
```bash
# Step 1: Install
pip install django-apcore[ninja]  # or [drf] or [all]

# Step 2: Add to INSTALLED_APPS
# settings.py: INSTALLED_APPS += ['django_apcore']

# Step 3: Scan + Serve
python manage.py apcore_scan --source ninja   # generate bindings
python manage.py apcore_serve                  # start MCP Server
```

### New Code
```python
from apcore import module
from myapp.models import User

@module(description="Create a new user", tags=["user"])
def create_user(name: str, email: str) -> dict:
    user = User.objects.create(name=name, email=email)
    return {"id": user.id, "name": user.name}
```

## Architecture

```
django-apcore Layered Architecture

+-----------------------------------------------------+
|  Output Layer (Unified Output)                       |
|  apcore Registry -> apcore-mcp-python                |
|  -> MCP Server (stdio / streamable-http)             |
|  -> OpenAI Tools                                     |
+------------------------+----------------------------+
                         |
+------------------------+----------------------------+
|  Core (django_apcore)                                |
|  Django App: settings + AppConfig + manage.py        |
|  Only depends on django + apcore + pydantic          |
+------+---------------+---------------+--------------+
       |               |               |
+------+------+ +------+------+ +------+------+
| Scanner:    | | Scanner:    | | Hand-written |
| django-     | | DRF +       | | @module      |
| ninja       | | spectacular | | decorator    |
| (optional)  | | (optional)  | |              |
+-------------+ +-------------+ +--------------+
```

### Dependency Design
```toml
[project]
dependencies = ["django>=4.2", "apcore>=0.2.0", "pydantic>=2.0"]

[project.optional-dependencies]
ninja = ["django-ninja>=1.0"]
drf = ["drf-spectacular>=0.27"]
mcp = ["apcore-mcp>=0.1.0"]
all = ["django-apcore[ninja,drf,mcp]"]
```

## MVP Scope (Confirmed)

### 1. Django App (django_apcore)
- `APCORE_*` settings configuration
- AppConfig: auto-discover and register apcore modules on startup
- apcore Registry bound to Django lifecycle

### 2. Scanner: django-ninja (Optional Dependency)
- Scan NinjaAPI endpoints
- Extract input/output schemas using Pydantic `model_json_schema()`
- Extract descriptions and tags using `api.get_openapi_schema()`
- Output: YAML binding files or Python decorator code

### 3. Scanner: DRF (Optional Dependency)
- Scan DRF ViewSet + drf-spectacular
- Extract OpenAPI 3.0 via `SchemaGenerator.get_schema()`
- Convert OpenAPI components/schemas to apcore module definitions
- Output: YAML binding files or Python decorator code

### 4. Management Commands
- `apcore_scan`
  - `--source ninja|drf` specify scan source
  - `--output yaml|python` specify output format (default yaml)
  - `--dir <path>` specify output directory
- `apcore_serve`
  - `--transport stdio|streamable-http` specify transport (default stdio)
  - `--host` / `--port` optional parameters

### 5. MCP Output (Optional Dependency)
- Via apcore-mcp-python's `serve()` function
- Supports stdio (Claude Desktop / Cursor direct connection)
- Supports streamable-http (remote deployment)

### Not in MVP
- Django Auth/Permission to apcore ACL mapping
- Django Middleware to apcore Middleware bridging
- Django Admin integration
- request/user context auto-injection
- Plain Django views scanner

## Differentiation vs Competitors

| Dimension | django-apcore | django-mcp-server | django-ninja-mcp | fastapi-mcp |
|------|--------------|-------------------|-------------------|-------------|
| Schema enforcement | **Mandatory** | None | Partial | Auto |
| Multi-output (MCP + OpenAI) | **Yes** | No | No | No |
| Protocol standard | **apcore** | Custom | None | None |
| DRF support | **Yes** | Yes | No | No |
| ninja support | **Yes** | No | Yes (stagnant) | No |
| Zero-intrusion scan | **Yes** | No | No | Partial |
| Django-specific | **Yes** | Yes | Yes | No |

## Success Criteria (MVP)
1. Existing django-ninja project: start MCP Server in 3 steps (no source code modifications)
2. Existing DRF project: start MCP Server in 3 steps (no source code modifications)
3. New code: `@module` decorator works, Django ORM usable within modules
4. Generated MCP Server can be successfully connected and invoked by Claude Desktop or Cursor

## Risks
1. **apcore protocol adoption unknown** -- extra abstraction layer may be rejected
2. **Naming / discoverability** -- searching "django mcp" will not find "django-apcore"
3. **80% of full-stack developers are not target users** -- actual addressable market is small
4. **DRF scanner complexity** -- many edge cases like SerializerMethodField

## Demand Validation Status
- [x] Problem backed by evidence
- [x] Target users identified and reachable
- [x] Existing solutions analyzed
- [x] "What if we don't build this?" answered
- [x] Demand evidence exists
- [x] Differentiation clear
- [x] MVP scope defined

## Session History
- Session 1 (2026-02-18): Exploration -- naming decision, core differentiation
- Session 2 (2026-02-18): Research -- competitive analysis (8+ packages), market data (82x gap)
- Session 3 (2026-02-18): Research -- decorator + YAML dual-path feasibility analysis
- Session 4 (2026-02-19): Validate -- Django user persona analysis, layered architecture finalized
- Session 5 (2026-02-19): Refine -- precise MVP scope, zero-intrusion 3-step experience

# django-apcore: Implementation Overview

## Overview

django-apcore is a thin-wrapper Django App (~1,500-2,000 lines) that bridges the apcore (AI-Perceivable Core) protocol to the Django ecosystem. It provides scanners that convert existing Django API endpoints (DRF ViewSets, django-ninja endpoints) into apcore module definitions, management commands for scanning and serving, and auto-discovery of modules on Django startup. All protocol logic delegates to the apcore SDK; all MCP transport logic delegates to apcore-mcp-python.

## Scope

### Included

- Django AppConfig with auto-discovery of YAML bindings and @module functions
- Settings validation for all `APCORE_*` configuration keys
- Singleton `apcore.Registry` wrapper
- BaseScanner ABC with `ScannedModule` dataclass
- NinjaScanner for django-ninja endpoints (optional dependency)
- DRFScanner for DRF ViewSets via drf-spectacular (optional dependency)
- YAMLWriter for generating `.binding.yaml` files
- PythonWriter for generating `@module` Python files
- `apcore_scan` management command for scan orchestration
- `apcore_serve` management command for MCP server orchestration
- Unit, integration, and fixture-based tests with strict TDD

### Excluded

- Django Auth/Permission to apcore ACL mapping
- Django Middleware bridging
- Django Admin integration
- Request/user context auto-injection
- Pure Django views scanner
- Database models or migrations
- Custom MCP transport implementation

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.10+ |
| Framework | Django | 4.2+ |
| Schema | Pydantic | 2.0+ |
| Protocol | apcore SDK | 0.2.0+ |
| MCP | apcore-mcp-python | 0.1.0+ |
| Testing | pytest + pytest-django | 8.0+ / 4.5+ |
| Linting | ruff | 0.4+ |
| Types | mypy | 1.10+ |
| Build | hatchling | 1.20+ |

## Task Execution Order

| # | Task File | Description | Status |
|---|-----------|-------------|--------|
| 1 | [tasks/001-setup.md](tasks/001-setup.md) | Project scaffold: pyproject.toml, directory structure, CI config, dev tools | Pending |
| 2 | [tasks/002-settings.md](tasks/002-settings.md) | ApcoreSettings: read/validate APCORE_* from Django settings | Pending |
| 3 | [tasks/003-registry.md](tasks/003-registry.md) | Registry wrapper: get_registry() singleton | Pending |
| 4 | [tasks/004-app-config.md](tasks/004-app-config.md) | ApcoreAppConfig: auto-discovery in ready() | Pending |
| 5 | [tasks/005-scanner-base.md](tasks/005-scanner-base.md) | BaseScanner ABC + ScannedModule dataclass | Pending |
| 6 | [tasks/006-output-writers.md](tasks/006-output-writers.md) | YAMLWriter + PythonWriter | Pending |
| 7 | [tasks/007-ninja-scanner.md](tasks/007-ninja-scanner.md) | NinjaScanner implementation | Pending |
| 8 | [tasks/008-drf-scanner.md](tasks/008-drf-scanner.md) | DRFScanner implementation | Pending |
| 9 | [tasks/009-scan-command.md](tasks/009-scan-command.md) | apcore_scan management command | Pending |
| 10 | [tasks/010-serve-command.md](tasks/010-serve-command.md) | apcore_serve management command + integration tests | Pending |

## Dependencies

### Required

- `apcore >= 0.2.0` -- Core protocol SDK (Registry, BindingLoader, @module, Executor)
- `django >= 4.2` -- Target web framework
- `pydantic >= 2.0` -- Schema definition (transitive via apcore)
- `pyyaml >= 6.0` -- YAML binding file I/O (transitive via apcore)

### Optional

- `django-ninja >= 1.0` -- Required for NinjaScanner (`pip install django-apcore[ninja]`)
- `drf-spectacular >= 0.27` -- Required for DRFScanner (`pip install django-apcore[drf]`)
- `apcore-mcp >= 0.1.0` -- Required for apcore_serve command (`pip install django-apcore[mcp]`)

### Development

- `pytest >= 8.0`
- `pytest-django >= 4.5`
- `ruff >= 0.4`
- `mypy >= 1.10`
- `hatchling >= 1.20`

## Reference Documents

- [Technical Design Document](../../docs/django-apcore/tech-design.md)
- [Product Requirements Document](../../docs/django-apcore/prd.md)

# Competitive Analysis: Django + MCP Integration Landscape

> Research date: 2026-02-18

## Executive Summary

The Django + MCP integration space is **fragmented but active**. There are at least **8 distinct Django MCP packages** on PyPI/GitHub, none of which has achieved dominant market position. The clear market leader in the broader Python MCP space is **fastapi-mcp** (11.5k stars, 4.3M downloads), which has no Django equivalent in scale. The most-downloaded Django package is **django-mcp-server** (1M+ downloads), but its star count (~274) suggests many of those downloads are automated/CI rather than organic adoption.

**Key finding for django-apcore**: The draft assumption that "Django has no MCP solution" is **incorrect** -- there are multiple solutions. However, none takes the approach django-apcore proposes (apcore protocol + django-ninja style decorators + Pydantic schema enforcement). The real gap is not "no solution exists" but rather "no opinionated, schema-first, protocol-driven solution exists."

---

## 1. Direct Django MCP Competitors

### 1.1 django-mcp-server (by gts360 / Smart GTS)

| Metric | Value |
|---|---|
| PyPI package | `django-mcp-server` |
| GitHub | [gts360/django-mcp-server](https://github.com/gts360/django-mcp-server) |
| Stars | ~274 |
| Forks | ~44 |
| Total Downloads | **1,006,408** (1M+) |
| Latest Version | 0.5.7 (Oct 2025) |
| License | MIT |
| Python | 3.10+ |
| Django | 4.x, 5.x |

**What it does:**
- Declarative-style tools for AI agents to interact with Django
- Exposes Django models for safe AI querying with minimal code
- Converts DRF APIs to MCP tools with one annotation (`@drf_serialize_output`)
- Works on both WSGI and ASGI
- Session management through Django's session framework
- OAuth2 authorization support
- STDIO transport for local dev (Claude Desktop compatible)
- Validated with Claude AI as a remote MCP integration

**What it does well:**
- Most mature Django MCP package by download count
- Dual WSGI/ASGI support is rare -- most competitors require ASGI
- DRF integration is practical for existing projects
- Active maintenance with multiple contributors

**What it does poorly:**
- Declarative style is custom/proprietary, not following any established pattern (not django-ninja style, not DRF standard)
- No Pydantic schema enforcement -- uses its own abstraction
- No protocol-level standard beyond MCP itself
- Documentation could be stronger
- High download count vs moderate star count suggests inflated metrics

**Target users:** Django developers with existing DRF APIs who want quick MCP exposure

---

### 1.2 django-mcp (by kitespark) -- PyPI name holder

| Metric | Value |
|---|---|
| PyPI package | `django-mcp` |
| GitHub | [kitespark/django-mcp](https://github.com/kitespark/django-mcp) |
| Stars | ~73 |
| Forks | ~9 |
| Total Downloads | **17,162** |
| Latest Version | 0.3.1 (May 2025) |
| License | MIT |
| Python | 3.10+ |
| Status | **ARCHIVED** (Oct 2025) |

**What it does:**
- Thin abstraction layer between Django and the official MCP Python SDK
- Exports `mcp_app` (upstream FastMCP instance) for direct use
- ASGI integration with Django-style URL path parameters
- Session caching and client reconnection handling
- MCP Inspector management command
- Async Django ORM support

**What it does well:**
- Clean, minimal design -- wraps the official SDK rather than reinventing
- Django-style URL parameters (`/mcp/<slug:user_uuid>`) are a nice touch
- Good async support
- Holds the `django-mcp` PyPI name

**What it does poorly:**
- **Archived** -- no longer maintained as of Oct 2025
- Thin wrapper means limited Django-specific value-add
- No model introspection, no DRF integration
- Small community (2 contributors)

**Target users:** Developers who want minimal abstraction over the MCP SDK

**Note for django-apcore:** The `django-mcp` PyPI name is taken but the project is archived. The `django-apcore` name avoids this conflict entirely.

---

### 1.3 django-mcp (by hyperb1iss) -- Different project, same-ish name

| Metric | Value |
|---|---|
| GitHub | [hyperb1iss/django-mcp](https://github.com/hyperb1iss/django-mcp) |
| Stars | ~13 |
| Forks | ~4 |
| License | Apache 2.0 |
| Status | Alpha |
| Last commit | Mar 2025 |

**What it does:**
- Decorator-based API for exposing Django models and functions to AI
- Auto-discovery of MCP components across Django apps
- Built-in ASGI server with SSE
- Dashboard at `/mcp/dashboard/`
- DRF compatibility
- Permission controls

**What it does well:**
- Decorator-based approach is closest to what django-apcore envisions
- Auto-discovery is a nice Django-native pattern
- Dashboard for visibility

**What it does poorly:**
- Very low adoption (13 stars)
- Alpha quality, last commit 11 months ago -- likely abandoned
- Name collision with the kitespark package
- Not on PyPI under its own name (or conflicts with kitespark's)

**Target users:** Developers who want decorator-based MCP exposure

---

### 1.4 mcp-django (by joshuadavidthomas)

| Metric | Value |
|---|---|
| PyPI package | `mcp-django` |
| GitHub | [joshuadavidthomas/mcp-django](https://github.com/joshuadavidthomas/mcp-django) |
| Stars | ~39 |
| Forks | ~2 |
| Total Downloads | **7,314** |
| Latest Version | 0.13.0 (Nov 2025) |
| License | MIT |
| Python | 3.10-3.14 |
| Django | 4.2-6.0 |

**What it does:**
- MCP server for Django project exploration (not for exposing business logic)
- Project discovery: apps, models, configuration
- Django Packages integration for browsing third-party packages
- Stateless Python shell execution
- Multi-transport: STDIO, HTTP, SSE
- Zero-config setup

**What it does well:**
- Unique angle: development-time tool, not runtime API exposure
- Broad Django version support (4.2 through 6.0)
- Well-maintained (0 open issues, active releases)
- Practical for AI-assisted development workflows

**What it does poorly:**
- **Explicitly not for production** -- provides shell access
- Does not expose business logic as MCP tools
- Different use case than django-apcore entirely

**Target users:** Developers using AI coding assistants (Cursor, Claude Code) who want their assistant to understand their Django project structure

**Relevance to django-apcore:** Low -- different problem space. mcp-django helps AI understand your code; django-apcore would help AI call your code.

---

### 1.5 django-rest-framework-mcp (by zacharypodbela)

| Metric | Value |
|---|---|
| PyPI package | `django-rest-framework-mcp` |
| GitHub | [zacharypodbela/django-rest-framework-mcp](https://github.com/zacharypodbela/django-rest-framework-mcp) |
| Stars | ~34 |
| Forks | ~5 |
| Total Downloads | **3,521** |
| Latest Version | 0.1.0a4 (Nov 2025) |
| License | Not specified |
| Last commit | Jan 2025 |

**What it does:**
- `@mcp_viewset` decorator converts DRF CRUD operations into MCP tools
- Schema inference from DRF serializers
- DRF authentication/permission enforcement on MCP requests
- Custom action support via `@mcp_tool` decorator
- STDIO transport via `mcp-remote` for Claude Desktop

**What it does well:**
- DRF-native approach is practical for the huge DRF user base
- Schema inference from serializers reduces boilerplate
- Security integration preserves existing auth setup
- Posted on Django Forum for community feedback

**What it does poorly:**
- Still in alpha (0.1.0a4)
- Low downloads, modest stars
- Last GitHub commit is over a year old (Jan 2025) -- possibly stale
- Tightly coupled to DRF -- cannot work without it

**Target users:** DRF developers who want their existing ViewSets exposed as MCP tools

---

### 1.6 drf-mcp (by ziyacivan)

| Metric | Value |
|---|---|
| PyPI package | `drf-mcp` |
| GitHub | [ziyacivan/drf-mcp](https://github.com/ziyacivan/drf-mcp) |
| Stars | ~0 |
| Total Downloads | Low (not tracked) |
| Latest Version | 0.1.1 (Jan 2026) |
| License | MIT |
| Contributors | 1 |

**What it does:**
- "Enterprise-grade" MCP integration for DRF with FastMCP 3.0
- Auto-discovers all DRF views/ViewSets from URLconf
- Uses drf-spectacular for JSON schema generation
- Async-first execution
- Supports stdio, HTTP, SSE transports

**What it does well:**
- Uses drf-spectacular (industry standard) for schema generation
- Async-first design
- Recent release (Jan 2026)

**What it does poorly:**
- Zero stars, single contributor -- essentially a personal project
- "Enterprise-grade" marketing with no adoption to back it up
- Duplicates django-rest-framework-mcp's concept

**Target users:** DRF developers (same as 1.5, but less proven)

---

### 1.7 django-ninja-mcp (by mikeedjones)

| Metric | Value |
|---|---|
| PyPI package | `django-ninja-mcp` |
| GitHub | [mikeedjones/django-ninja-mcp](https://github.com/mikeedjones/django-ninja-mcp) |
| Stars | ~13 |
| Forks | ~2 |
| Total Downloads | Low |
| Latest Version | 0.0.1a2 (Apr 2025) |
| License | MIT |
| Status | Early alpha, unstable API |

**What it does:**
- Automatic MCP server generator for Django Ninja applications
- Converts Django Ninja API endpoints into MCP tools
- OpenAPI integration for rich tool descriptions
- SSE transport
- Filtering by operations or tags

**What it does well:**
- Directly relevant to django-apcore's django-ninja dependency
- Leverages OpenAPI schema (django-ninja's strength)
- Clean concept: your existing Ninja API becomes MCP tools

**What it does poorly:**
- Depends on an **unmerged Django Ninja PR** -- cannot work with released django-ninja
- Very early alpha, unstable API warning
- Low adoption (13 stars)
- Last commit Apr 2025 -- 10 months stale
- There's an open [feature request on django-ninja](https://github.com/vitalik/django-ninja/issues/1449) for this functionality, suggesting the maintainer hasn't committed to it

**Target users:** Django Ninja users who want their APIs as MCP tools

**Critical relevance to django-apcore:** This is the closest existing project to django-apcore's vision. However, it takes a different approach -- it converts existing django-ninja endpoints to MCP tools (API-first), whereas django-apcore defines apcore modules that happen to be in Django (protocol-first). Also, django-ninja-mcp appears abandoned.

---

### 1.8 django-ai-boost (by Vinta Software)

| Metric | Value |
|---|---|
| GitHub | [vintasoftware/django-ai-boost](https://github.com/vintasoftware/django-ai-boost) |
| Stars | ~75 |
| Forks | ~2 |
| License | MIT |
| Status | Active |

**What it does:**
- MCP server for **developing** Django applications (dev-time tool)
- Project discovery: models, URLs, management commands
- Database introspection: schema, migrations, relationships
- Configuration access via dot notation
- Log reading with filtering
- Bearer token auth for SSE transport
- Read-only operations only

**What it does well:**
- From Vinta Software (respected Django consultancy)
- Practical dev-time tool with good feature set
- Solid security model (read-only, auth required)
- Good MCP client compatibility (Cursor, Claude Desktop, GitHub Copilot, etc.)
- Part of a broader Django AI ecosystem (django-ai-assistant, django-ai-plugins)

**What it does poorly:**
- Dev-time only -- not for runtime business logic exposure
- Different problem space than django-apcore

**Target users:** Developers using AI assistants for Django development

**Relevance to django-apcore:** Complementary, not competitive. django-ai-boost helps you build; django-apcore would help AI call what you built.

---

### 1.9 django-mcpx (by synw)

| Metric | Value |
|---|---|
| GitHub | [synw/django-mcpx](https://github.com/synw/django-mcpx) |
| Stars | ~2 |
| Last commit | Jan 2025 |
| License | MIT |

**What it does:**
- Compose MCP servers in Django using FastMCP
- Django settings-based configuration
- Built-in auth with bearer tokens
- Management command to run MCP servers

**What it does well:**
- Simple integration approach
- Django settings-based config is idiomatic

**What it does poorly:**
- Essentially abandoned (2 stars, no activity)
- Minimal documentation
- Very thin wrapper

---

## 2. Non-Django Python MCP Frameworks

### 2.1 fastapi-mcp (by tadata-org) -- THE market leader

| Metric | Value |
|---|---|
| PyPI package | `fastapi-mcp` |
| GitHub | [tadata-org/fastapi_mcp](https://github.com/tadata-org/fastapi_mcp) |
| Stars | **11,500+** |
| Forks | **904** |
| Total Downloads | **4,337,622** (4.3M+) |
| Contributors | 15 |
| Latest Version | 0.4.0 (Jul 2025) |
| License | MIT |
| Last commit | Feb 18, 2026 (today) |
| Open Issues | 78 |

**What it does:**
- Automatically exposes FastAPI endpoints as MCP tools
- Zero/minimal configuration -- point at your FastAPI app and it works
- Preserves request/response model schemas and documentation
- Built-in auth via FastAPI dependency injection
- Native ASGI transport (no separate HTTP calls)
- Flexible deployment: co-located or separate servers

**What it does well:**
- **Dominant market position** -- 30x more stars than any Django competitor
- Hit #1 trending on GitHub for Python (Aug 2025)
- Active development (commit today)
- Large contributor base
- Clean, FastAPI-native design philosophy
- "Just works" approach resonates with developers

**What it does poorly:**
- FastAPI-only -- Django developers cannot use it
- 78 open issues suggest scaling challenges
- Tightly coupled to FastAPI's ASGI model

**Why it matters for django-apcore:** fastapi-mcp is the existence proof that framework-specific MCP integration is a real, high-demand product category. It also represents the **pull factor** that draws Django developers toward FastAPI for MCP use cases. django-apcore could cite fastapi-mcp's success as validation while positioning as "fastapi-mcp for Django, but better" (protocol-driven, schema-first).

---

### 2.2 MCP Python SDK (Official)

| Metric | Value |
|---|---|
| PyPI package | `mcp` |
| GitHub | [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) |
| Stars | **21,700+** |
| Forks | **3,100+** |
| Latest Version | 1.26.0 (Jan 2026) |
| License | MIT |

**What it does:**
- Official Python implementation of MCP
- FastMCP high-level API with decorators
- Supports stdio, SSE, Streamable HTTP transports
- Resources, Tools, Prompts primitives
- Client and server implementations

**Relevance:** This is the foundation that nearly all Django MCP packages build upon. django-apcore would not use this directly (it would go through apcore-mcp-python), which is a meaningful architectural distinction.

---

### 2.3 flask-mcp-server (by bashar94)

| Metric | Value |
|---|---|
| PyPI package | `flask-mcp-server` |
| GitHub | [bashar94/flask-mcp-server](https://github.com/bashar94/flask-mcp-server) |
| Stars | ~2 |
| Total Downloads | **2,038** |
| Latest Version | 0.6.1 (Aug 2025) |
| License | MIT |

**What it does:**
- Flask-based MCP server with security features
- Unified `/mcp` endpoint (POST for JSON-RPC, GET for SSE)
- API key + HMAC auth, rate limiting
- Tools with roles and TTL cache
- MCP 2025-06-18 spec compliance

**Assessment:** Very low adoption. Flask's synchronous nature is a poor fit for MCP's streaming requirements.

---

### 2.4 FlaskMCP (by Vprashant)

| Metric | Value |
|---|---|
| PyPI package | `flaskmcp` |
| Latest Version | 0.1.2 (Apr 2025) |
| Status | Beta |

**What it does:**
- Flask-based MCP implementation
- Tool registry, resource management, prompt templates
- JSON Schema validation
- OpenAPI auto-docs

**Assessment:** Minimal adoption, beta quality, no significant traction.

---

### 2.5 mcp-utils (by fulfilio)

| Metric | Value |
|---|---|
| GitHub | [fulfilio/mcp-utils](https://github.com/fulfilio/mcp-utils) |

**What it does:**
- Synchronous MCP server helpers for Flask
- Designed for developers who want MCP without async complexity

**Assessment:** Niche utility, not a framework.

---

## 3. Adjacent / Complementary Projects

### 3.1 django-ai-assistant (by Vinta Software)

| Metric | Value |
|---|---|
| GitHub | [vintasoftware/django-ai-assistant](https://github.com/vintasoftware/django-ai-assistant) |

- Integrates AI assistants with Django using LangChain
- Tool calling and RAG support
- Not MCP-based -- uses LangChain's tool calling
- Different approach: AI calls Django vs Django exposes MCP

### 3.2 FastMCP (by jlowin)

| Metric | Value |
|---|---|
| GitHub | [jlowin/fastmcp](https://github.com/jlowin/fastmcp) |
| PyPI | `fastmcp` |

- High-level Pythonic framework for building MCP servers
- Not framework-specific
- Many Django MCP packages build on top of this
- The "de facto" way to build MCP servers in Python

---

## 4. Comparative Matrix

| Package | Stars | Downloads | Django Version | Approach | Active? | DRF? | Pydantic? | Schema-first? |
|---|---|---|---|---|---|---|---|---|
| django-mcp-server | 274 | 1M+ | 4-5 | Declarative tools | Yes | Yes | No | No |
| django-ai-boost | 75 | N/A | Active | Dev-time introspection | Yes | No | No | No |
| django-mcp (kitespark) | 73 | 17K | 4.1+ | SDK wrapper | **Archived** | No | No | No |
| mcp-django | 39 | 7.3K | 4.2-6.0 | Project exploration | Yes | No | No | No |
| django-rest-framework-mcp | 34 | 3.5K | N/A | DRF ViewSet decorator | Stale | Yes | No | No |
| django-ninja-mcp | 13 | Low | N/A | Ninja endpoint conversion | Stale | No | Via Ninja | Partial |
| hyperb1iss/django-mcp | 13 | N/A | N/A | Decorator-based | Stale | Yes | No | No |
| drf-mcp | 0 | Low | 4.2+ / 5.0+ | DRF auto-discovery | New | Yes | No | No |
| django-mcpx | 2 | Low | N/A | FastMCP compose | Stale | No | No | No |
| **fastapi-mcp** (reference) | **11,500** | **4.3M** | N/A | FastAPI endpoint conversion | **Very active** | N/A | Yes | Yes |

---

## 5. Key Insights for django-apcore

### 5.1 The Draft's Assumption Was Wrong (But the Opportunity Is Real)

The draft states: "The Django ecosystem currently has no MCP / AI-Perceivable module solution". This is factually incorrect -- there are 8+ packages. **However**, the opportunity is real because:

1. **No dominant player**: The highest-starred Django package (274 stars) has 2.4% of fastapi-mcp's stars
2. **Fragmentation**: 8+ packages solving similar problems = confusion, not clarity
3. **No protocol-level thinking**: Every existing package is "add MCP to Django." None proposes a module definition standard
4. **No schema-first approach**: Only django-ninja-mcp (abandoned) comes close to Pydantic schema enforcement

### 5.2 What Existing Solutions Miss

| Gap | Detail |
|---|---|
| **No protocol standard** | All packages are MCP transport layers. None defines a module contract (input_schema, output_schema, description enforcement) |
| **No portability** | Tools defined in django-mcp-server cannot be exported as OpenAI Tools or used outside MCP |
| **No schema enforcement** | Most packages auto-discover endpoints rather than enforcing explicit schemas |
| **No django-ninja alignment** | Despite django-ninja's popularity, only one abandoned alpha package bridges the two |
| **DRF-heavy bias** | Most solutions assume DRF. Modern Django developers increasingly use django-ninja or plain Django |

### 5.3 django-apcore's Potential Differentiators

1. **Protocol-first (apcore)**: Not just "MCP transport for Django" but "define AI-perceivable modules in Django that can be exposed via any protocol"
2. **Multi-output**: Same module definition works as MCP Server AND OpenAI Tools (via apcore-mcp-python)
3. **Schema enforcement**: Mandatory input_schema/output_schema/description (apcore spec)
4. **django-ninja style**: Familiar decorator + Pydantic pattern for Django developers
5. **Not just DRF**: Works with plain Django, django-ninja, or DRF

### 5.4 Risks and Concerns

| Risk | Detail |
|---|---|
| **apcore adoption** | apcore is a new protocol with unknown community adoption. All competitors use MCP directly. django-apcore adds an abstraction layer (apcore) between Django and MCP -- developers may prefer direct MCP |
| **django-ninja dependency** | Requiring django-ninja narrows the user base. Most existing solutions work with plain Django |
| **Market timing** | The Django MCP space is already crowded. Late entry needs strong differentiation |
| **"Not invented here" resistance** | Django community may prefer contributing to existing packages over adopting a new one |
| **Naming confusion** | "apcore" is not self-explanatory. Developers searching for "django mcp" will not find "django-apcore" |

### 5.5 What "If We Don't Build This" Looks Like

Django developers who want MCP today will:
1. Use **django-mcp-server** (most mature, 1M+ downloads) for DRF-based projects
2. Use **mcp-django** for dev-time AI assistant integration
3. Use the **official MCP Python SDK** directly with manual Django integration
4. Switch to **FastAPI + fastapi-mcp** for greenfield projects (the real threat)

The strongest argument for django-apcore is **option 4** -- preventing Django developer migration to FastAPI for AI integration use cases. But this argument requires django-apcore to be significantly better than existing Django MCP packages, not just different.

---

## 6. Recommendations

1. **Validate apcore protocol demand independently** before building django-apcore. If apcore itself has no adoption, django-apcore inherits that problem.

2. **Consider whether django-ninja should be optional** rather than required. The most successful Django MCP package (django-mcp-server) works with plain Django.

3. **SEO/discoverability**: Ensure "django mcp" appears prominently in package description and README, since "apcore" alone will not be discovered by developers searching for MCP solutions.

4. **Position against fastapi-mcp explicitly**: "The fastapi-mcp experience, for Django" is a more compelling pitch than "apcore protocol implementation for Django."

5. **Study django-mcp-server's success**: At 1M+ downloads, understand what drove its adoption -- it likely benefited from being early and practical rather than architecturally elegant.

---

## Sources

- [django-mcp (kitespark) on PyPI](https://pypi.org/project/django-mcp/)
- [django-mcp (kitespark) on GitHub](https://github.com/kitespark/django-mcp)
- [django-mcp (hyperb1iss) on GitHub](https://github.com/hyperb1iss/django-mcp)
- [django-mcp-server on PyPI](https://pypi.org/project/django-mcp-server/)
- [django-mcp-server on GitHub](https://github.com/gts360/django-mcp-server)
- [mcp-django on PyPI](https://pypi.org/project/mcp-django/)
- [mcp-django on GitHub](https://github.com/joshuadavidthomas/mcp-django)
- [django-rest-framework-mcp on GitHub](https://github.com/zacharypodbela/django-rest-framework-mcp)
- [django-rest-framework-mcp on Django Forum](https://forum.djangoproject.com/t/django-rest-framework-mcp-expose-your-django-apis-to-ai-agents-like-claude-with-a-few-lines-of-code/42758)
- [drf-mcp on Libraries.io](https://libraries.io/pypi/drf-mcp)
- [django-ninja-mcp on PyPI](https://pypi.org/project/django-ninja-mcp/)
- [django-ninja-mcp on GitHub](https://github.com/mikeedjones/django-ninja-mcp)
- [django-ninja MCP feature request](https://github.com/vitalik/django-ninja/issues/1449)
- [django-ai-boost on GitHub](https://github.com/vintasoftware/django-ai-boost)
- [django-ai-assistant on GitHub](https://github.com/vintasoftware/django-ai-assistant)
- [django-mcpx on GitHub](https://github.com/synw/django-mcpx)
- [fastapi-mcp on PyPI](https://pypi.org/project/fastapi-mcp/)
- [fastapi-mcp on GitHub](https://github.com/tadata-org/fastapi_mcp)
- [How FastAPI-MCP hit #1 Trending on GitHub](https://medium.com/@miki_45906/how-fastapi-mcp-hit-1-trending-on-github-python-a9a660f48125)
- [MCP Python SDK on GitHub](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Python SDK Documentation](https://modelcontextprotocol.github.io/python-sdk/)
- [flask-mcp-server on PyPI](https://pypi.org/project/flask-mcp-server/)
- [flask-mcp-server on GitHub](https://github.com/bashar94/flask-mcp-server)
- [flaskmcp on PyPI](https://pypi.org/project/flaskmcp/)
- [mcp-utils on GitHub](https://github.com/fulfilio/mcp-utils)
- [Django AI Boost blog post](https://www.vintasoftware.com/blog/django-ai-boost-productivity)
- [Django MCP implementation blog (Agent Interviews)](https://docs.agentinterviews.com/blog/mcp-server-django-implementation/)
- [pepy.tech download stats](https://pepy.tech/)
- [Django Packages: Django MCP Server](https://djangopackages.org/packages/p/django-mcp-server/)

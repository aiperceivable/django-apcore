# Market Research — django-apcore
> Last updated: 2026-02-18

## Django Developer Market Size

| Metric | Value | Source |
|--------|-------|--------|
| Django PyPI monthly downloads | ~25.5M | PyPI Stats |
| Companies using Django | 42,880+ | 6Sense |
| Django market share (web frameworks) | 32.90% | 6Sense |
| Django devs using ChatGPT | 69% | State of Django 2025 |
| Django devs using Claude | 15% | State of Django 2025 |
| Django devs using AI for learning | 38% | State of Django 2025 |
| All devs using AI regularly | 93% | JetBrains AI Pulse 2026 |

## django-ninja Adoption

| Metric | Value |
|--------|-------|
| PyPI monthly downloads | 1,352,223 |
| GitHub stars | ~8,659 |

## MCP Protocol Adoption

| Metric | Value | Date |
|--------|-------|------|
| MCP servers (active) | 10,000+ | Dec 2025 |
| Monthly SDK downloads (Python + TS) | 97M | Dec 2025 |
| FastMCP monthly downloads | 17.3M | Feb 2026 |
| fastapi-mcp monthly downloads | 4.6M | Feb 2026 |
| MCP clients | 300-519 | 2025 |
| Agent orchestration market (projected) | $30B by 2030 | 2025 |

### Corporate MCP Adoption Timeline
- Nov 2024: Anthropic open-sources MCP
- Mar 2025: OpenAI adopts MCP
- Apr 2025: Google DeepMind confirms Gemini support
- 2025: Microsoft, Cloudflare, Vercel, Netlify add support
- 2026 projection: 75% of API gateway vendors expected to have MCP features

## The FastAPI vs Django MCP Gap

| | fastapi-mcp | All Django MCP packages combined |
|---|---|---|
| Monthly Downloads | 4,627,345 | ~56,600 |
| Ratio | **82x more** | 1x |

Django's MCP ecosystem gets only 1.2% of what FastAPI's gets, despite Django itself having more total downloads.

## Community Signals

### Django Forum
- 4+ MCP-related threads (Sep 2025 - Feb 2026)
- Django core contributor positive on MCP: "I think it would be worth working on"
- Low engagement: 1-7 replies per thread

### DjangoCon US 2025
- Keynote: "Django Reimagined For The Age of AI" (Marlene Mhangami, Microsoft) — included MCP demo
- Talk: "Django for AI" (Will Vincent)

### django-ninja Issue #1449
- Feature request for MCP support — 8 upvotes
- Maintainer (vitalik) **declined**: "MCP tools are most often completely different than regular rest"
- Explicitly pushed MCP to third-party packages

### Weak Signals
- Reddit: No Django+MCP discussions found
- Stack Overflow: No Django+MCP questions found
- Twitter/X: No indexed discussions found

## Key Insight
The django-ninja maintainer explicitly refusing to build MCP in and pushing to external packages is actually **validation** for django-apcore — it confirms the need exists AND creates a market opportunity for a dedicated package.

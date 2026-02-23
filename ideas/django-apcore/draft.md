# django-apcore

> Status: Ready | Draft v4 | 2026-02-19

## One-Liner
Django 的 apcore 实现 — 零侵入，3 步让已有 Django 项目变成 MCP Server。

## Problem
Django 的 MCP 生态严重碎片化（8+ 个包，无主导者），所有现有方案都只是 MCP 传输层，缺少协议级模块定义标准。fastapi-mcp 下载量是所有 Django MCP 包总和的 82 倍，Django 开发者面临向 FastAPI 迁移的压力。

## Target Users
三类用户，分层服务：

| 用户类型 | 占 Django 社区 | 入口方式 | 额外依赖 |
|---------|---------------|---------|---------|
| 新代码 / ML 团队 | ~8-10% | `@module` 装饰器 | 无 |
| DRF API 用户 | ~49% | `manage.py apcore_scan --source drf` | drf-spectacular |
| django-ninja 用户 | ~10% (+67% YoY) | `manage.py apcore_scan --source ninja` | django-ninja |

## Core Experience（零侵入，3 步上手）

### 已有项目
```bash
# Step 1: 安装
pip install django-apcore[ninja]  # 或 [drf] 或 [all]

# Step 2: 加入 INSTALLED_APPS
# settings.py: INSTALLED_APPS += ['django_apcore']

# Step 3: 扫描 + 启动
python manage.py apcore_scan --source ninja   # 生成 binding
python manage.py apcore_serve                  # 启动 MCP Server
```

### 新代码
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
django-apcore 分层架构

┌─────────────────────────────────────────────────────┐
│  Output Layer (统一输出)                              │
│  apcore Registry → apcore-mcp-python                 │
│  → MCP Server (stdio / streamable-http)              │
│  → OpenAI Tools                                      │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│  Core (django_apcore)                                │
│  Django App: settings + AppConfig + manage.py        │
│  只依赖 django + apcore + pydantic                   │
└──────┬──────────────┬──────────────┬────────────────┘
       │              │              │
┌──────┴─────┐ ┌──────┴─────┐ ┌─────┴──────┐
│ Scanner:   │ │ Scanner:   │ │ 手写       │
│ django-    │ │ DRF +      │ │ @module    │
│ ninja      │ │ spectacular│ │ 装饰器     │
│ (可选)     │ │ (可选)     │ │            │
└────────────┘ └────────────┘ └────────────┘
```

### 依赖设计
```toml
[project]
dependencies = ["django>=4.2", "apcore>=0.2.0", "pydantic>=2.0"]

[project.optional-dependencies]
ninja = ["django-ninja>=1.0"]
drf = ["drf-spectacular>=0.27"]
mcp = ["apcore-mcp>=0.1.0"]
all = ["django-apcore[ninja,drf,mcp]"]
```

## MVP Scope（已确认）

### 1. Django App (django_apcore)
- `APCORE_*` settings 配置项
- AppConfig：启动时自动发现并注册 apcore 模块
- apcore Registry 与 Django 生命周期绑定

### 2. Scanner: django-ninja（可选依赖）
- 扫描 NinjaAPI 端点
- 利用 Pydantic `model_json_schema()` 提取 input/output schema
- 利用 `api.get_openapi_schema()` 提取描述、标签
- 输出：YAML binding 文件 或 Python 装饰器代码

### 3. Scanner: DRF（可选依赖）
- 扫描 DRF ViewSet + drf-spectacular
- 利用 `SchemaGenerator.get_schema()` 提取 OpenAPI 3.0
- 将 OpenAPI components/schemas 转为 apcore module 定义
- 输出：YAML binding 文件 或 Python 装饰器代码

### 4. Management Commands
- `apcore_scan`
  - `--source ninja|drf` 指定扫描来源
  - `--output yaml|python` 指定输出格式（默认 yaml）
  - `--dir <path>` 指定输出目录
- `apcore_serve`
  - `--transport stdio|streamable-http` 指定传输方式（默认 stdio）
  - `--host` / `--port` 可选参数

### 5. MCP 输出（可选依赖）
- 通过 apcore-mcp-python 的 `serve()` 函数
- 支持 stdio（Claude Desktop / Cursor 直连）
- 支持 streamable-http（远程部署）

### 不在 MVP 内
- Django Auth/Permission → apcore ACL 映射
- Django Middleware → apcore Middleware 桥接
- Django Admin 集成
- request/user 上下文自动注入
- 纯 Django views 扫描器

## Differentiation vs Competitors

| 维度 | django-apcore | django-mcp-server | django-ninja-mcp | fastapi-mcp |
|------|--------------|-------------------|-------------------|-------------|
| Schema 强制 | **强制** | 无 | 部分 | 自动 |
| 多输出（MCP + OpenAI） | **是** | 否 | 否 | 否 |
| 协议标准 | **apcore** | 自定义 | 无 | 无 |
| DRF 支持 | **是** | 是 | 否 | 否 |
| ninja 支持 | **是** | 否 | 是（停滞） | 否 |
| 零侵入扫描 | **是** | 否 | 否 | 部分 |
| Django 专用 | **是** | 是 | 是 | 否 |

## Success Criteria (MVP)
1. 已有 django-ninja 项目：3 步内启动 MCP Server（不修改原代码）
2. 已有 DRF 项目：3 步内启动 MCP Server（不修改原代码）
3. 新代码：`@module` 装饰器可用，模块内可正常使用 Django ORM
4. 生成的 MCP Server 可被 Claude Desktop 或 Cursor 成功连接和调用

## Risks
1. **apcore 协议采用率未知** — 额外抽象层可能被拒绝
2. **命名/可发现性** — 搜索 "django mcp" 找不到 "django-apcore"
3. **80% 全栈开发者不是目标用户** — 真实可触达市场较小
4. **DRF 扫描器复杂度** — SerializerMethodField 等边界情况多

## Demand Validation Status
- [x] Problem backed by evidence
- [x] Target users identified and reachable
- [x] Existing solutions analyzed
- [x] "What if we don't build this?" answered
- [x] Demand evidence exists
- [x] Differentiation clear
- [x] MVP scope defined

## Session History
- Session 1 (2026-02-18): Exploration — 确定命名，核心差异化
- Session 2 (2026-02-18): Research — 竞品分析（8+ 包），市场数据（82x 差距）
- Session 3 (2026-02-18): Research — 装饰器 + YAML 双路径可行性分析
- Session 4 (2026-02-19): Validate — Django 用户画像分析，确定分层架构
- Session 5 (2026-02-19): Refine — 确定 MVP 精确范围，零侵入 3 步体验

"""JSON API endpoints for the explorer.

Provides:
- GET  <prefix>/modules/           — list all registered modules
- GET  <prefix>/modules/<id>       — module detail with schemas
- POST <prefix>/modules/<id>/call  — execute a module (if allowed)
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from django_apcore.registry import get_context_factory, get_executor, get_registry
from django_apcore.settings import get_apcore_settings


def _annotations_to_dict(annotations: Any) -> dict[str, Any] | None:
    """Convert annotations to a plain dict."""
    if annotations is None:
        return None
    if isinstance(annotations, dict):
        return annotations
    if dataclasses.is_dataclass(annotations) and not isinstance(annotations, type):
        return dataclasses.asdict(annotations)
    return None


def _make_serializable(obj: object) -> object:
    """Recursively convert non-JSON-serializable objects (e.g. Pydantic models)."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    return obj


@require_GET
def list_modules(request):
    """List all registered modules with summary metadata."""
    registry = get_registry()
    modules = []
    for module_id, module in registry.iter():
        metadata = getattr(module, "metadata", None) or {}
        entry = {
            "module_id": module_id,
            "description": getattr(module, "description", ""),
            "tags": list(getattr(module, "tags", None) or []),
            "http_method": metadata.get("http_method", ""),
            "url_rule": metadata.get("url_rule", ""),
            "version": getattr(module, "version", "1.0.0"),
        }
        modules.append(entry)
    return JsonResponse(modules, safe=False)


@require_GET
def get_module(request, module_id):
    """Get detailed information for a single module including schemas."""
    registry = get_registry()
    descriptor = registry.get_definition(module_id)
    if descriptor is None:
        return JsonResponse(
            {"error": f"Module '{module_id}' not found"}, status=404
        )

    annotations_dict = _annotations_to_dict(descriptor.annotations)

    result = {
        "module_id": descriptor.module_id,
        "description": descriptor.description,
        "documentation": descriptor.documentation,
        "tags": descriptor.tags,
        "version": descriptor.version,
        "annotations": annotations_dict,
        "metadata": descriptor.metadata,
        "http_method": descriptor.metadata.get("http_method", ""),
        "url_rule": descriptor.metadata.get("url_rule", ""),
        "input_schema": descriptor.input_schema,
        "output_schema": descriptor.output_schema,
    }
    return JsonResponse(result)


@csrf_exempt
@require_POST
def call_module(request, module_id):
    """Execute a module and return the result.

    Returns 403 if APCORE_EXPLORER_ALLOW_EXECUTE is False.
    """
    settings = get_apcore_settings()
    if not settings.explorer_allow_execute:
        return JsonResponse(
            {
                "error": "Module execution is disabled. "
                "Set APCORE_EXPLORER_ALLOW_EXECUTE=True to enable."
            },
            status=403,
        )

    from apcore.errors import ModuleNotFoundError as ApcoreNotFound
    from apcore.errors import SchemaValidationError

    try:
        inputs = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    executor = get_executor()
    context = get_context_factory().create_context(request)

    try:
        output = executor.call(module_id, inputs, context)
    except ApcoreNotFound:
        return JsonResponse(
            {"error": f"Module '{module_id}' not found"}, status=404
        )
    except SchemaValidationError as e:
        return JsonResponse(
            {"error": f"Input validation failed: {e}"}, status=400
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"output": _make_serializable(output)})

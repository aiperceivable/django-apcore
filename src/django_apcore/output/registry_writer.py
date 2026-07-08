"""Django-aware registry writer.

Extends apcore-toolkit's RegistryWriter to handle Django view functions
whose first parameter is ``request`` (without type annotations).
"""

from __future__ import annotations

import contextlib
import inspect
import logging
from typing import TYPE_CHECKING, Any

from apcore_toolkit.output.registry_writer import RegistryWriter

if TYPE_CHECKING:
    from apcore_toolkit.types import ScannedModule

logger = logging.getLogger("django_apcore")


class DjangoRegistryWriter(RegistryWriter):
    """Registry writer that adapts Django view functions for apcore.

    Django view functions have a ``request`` parameter as their first
    argument, which apcore's ``FunctionModule`` cannot introspect (no type
    hint). This writer creates a schema-typed wrapper that bypasses
    function introspection entirely.

    Also handles the common case where modules are already registered
    by auto-discovery on Django startup — existing modules are replaced
    instead of raising a duplicate error.
    """

    def write(
        self,
        modules: list[ScannedModule],
        registry: Any,
        *,
        dry_run: bool = False,
        verify: bool = False,
        verifiers: Any = None,
        allowed_prefixes: list[str] | None = None,
    ) -> list[Any]:
        """Register scanned modules, replacing any that already exist."""
        from apcore_toolkit.output.types import WriteResult
        from apcore_toolkit.output.verifiers import (
            RegistryVerifier,
            run_verifier_chain,
        )

        results: list[WriteResult] = []
        for mod in modules:
            if dry_run:
                results.append(WriteResult(module_id=mod.module_id))
                continue

            fm = self._to_function_module(mod, allowed_prefixes=allowed_prefixes)

            # Unregister first if already exists (auto-discovery may have
            # registered from YAML bindings on startup)
            with contextlib.suppress(Exception):
                registry.unregister(mod.module_id)
            registry.register(mod.module_id, fm)
            logger.debug("Registered module: %s", mod.module_id)

            result = WriteResult(module_id=mod.module_id)
            if verify:
                vr = RegistryVerifier(registry).verify("", mod.module_id)
                if not vr.ok:
                    result = WriteResult(
                        module_id=mod.module_id,
                        verified=False,
                        verification_error=vr.error,
                    )
            if result.verified and verifiers:
                chain_result = run_verifier_chain(verifiers, "", mod.module_id)
                if not chain_result.ok:
                    result = WriteResult(
                        module_id=result.module_id,
                        path=result.path,
                        verified=False,
                        verification_error=chain_result.error,
                    )
            results.append(result)
        return results

    # NOTE: this writer no longer overrides ``_to_function_module`` — doing so
    # dropped ``annotations`` and silently disabled approval/ACL gating (that
    # keys on ``requires_approval``) for scanned Django routes. Field mapping,
    # including annotations, is centralized in the toolkit base writer's
    # ``_build_function_module``; here we override only the narrow hooks.

    def _adapt_func(self, func: Any, mod: ScannedModule) -> Any:
        """Strip a leading ``request`` parameter from Django view functions —
        apcore's ``FunctionModule`` cannot introspect the untyped ``request``.
        Applied before the base writer's Pydantic flattening."""
        params = list(inspect.signature(func).parameters.keys())
        if params and params[0] == "request":
            return _adapt_view_func(func)
        return func

    def _build_input_schema(self, mod: ScannedModule) -> Any:
        """Explicit input model from the scanned JSON Schema so
        ``FunctionModule`` skips function introspection."""
        return _schema_to_pydantic(f"{mod.module_id}_Input", mod.input_schema)

    def _build_output_schema(self, mod: ScannedModule) -> Any:
        """Explicit output model from the scanned JSON Schema."""
        return _schema_to_pydantic(f"{mod.module_id}_Output", mod.output_schema)


def _adapt_view_func(func: Any) -> Any:
    """Strip the ``request`` parameter from a Django view function.

    Creates a thin wrapper that supplies a dummy HttpRequest and
    unwraps (status_code, data) tuple returns from django-ninja views.

    Preserves the original function's parameter signature (minus ``request``)
    and resolves stringified annotations (PEP 563) so that downstream
    ``flatten_pydantic_params`` can detect Pydantic BaseModel parameters.
    """
    import typing

    orig_func = func
    sig = inspect.signature(func)

    # Build new signature without 'request'
    new_params = [p for name, p in sig.parameters.items() if name != "request"]
    new_sig = sig.replace(parameters=new_params)

    def adapted(**kwargs: Any) -> dict:
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        result = orig_func(request, **kwargs)
        if isinstance(result, tuple) and len(result) == 2:
            return result[1]
        return result

    adapted.__name__ = func.__name__
    adapted.__module__ = func.__module__
    adapted.__doc__ = func.__doc__
    adapted.__wrapped__ = func
    adapted.__signature__ = new_sig

    # Resolve stringified annotations (PEP 563) to real types so that
    # flatten_pydantic_params can detect Pydantic BaseModel parameters.
    try:
        resolved = typing.get_type_hints(func)
    except Exception:
        resolved = getattr(func, "__annotations__", {})

    adapted.__annotations__ = {k: v for k, v in resolved.items() if k != "request"}
    adapted.__annotations__["return"] = dict
    return adapted


_JSON_TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _schema_to_pydantic(name: str, schema: dict[str, Any]) -> Any:
    """Create a dynamic Pydantic model from a JSON Schema dict.

    Returns a ``type[BaseModel]`` that can be passed to
    ``FunctionModule(input_schema=...)`` to skip function introspection.
    """
    from pydantic import create_model

    properties = schema.get("properties", {})
    if not properties:
        # Empty schema — create a model with no fields
        return create_model(name)

    required = set(schema.get("required", []))
    fields: dict[str, Any] = {}

    for field_name, field_schema in properties.items():
        py_type = _JSON_TYPE_MAP.get(field_schema.get("type", ""), Any)
        if field_name in required:
            fields[field_name] = (py_type, ...)
        else:
            fields[field_name] = (py_type | None, None)

    return create_model(name, **fields)

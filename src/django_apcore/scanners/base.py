"""Base scanner interface and ScannedModule dataclass.

Re-exports from apcore-toolkit for backwards compatibility.
All scanners (NinjaScanner, DRFScanner) extend BaseScanner and produce
lists of ScannedModule instances.
"""

from dataclasses import replace
from typing import Any

from apcore_toolkit.openapi import (
    extract_input_schema,
    extract_output_schema,
    resolve_ref,
    resolve_schema,
)
from apcore_toolkit.scanner import BaseScanner
from apcore_toolkit.types import ScannedModule

__all__ = [
    "BaseScanner",
    "ScannedModule",
    "apply_effective_proxy_inputs",
    "extract_input_schema",
    "extract_output_schema",
    "resolve_ref",
    "resolve_schema",
]


def apply_effective_proxy_inputs(
    modules: list[ScannedModule], specs: list[dict[str, Any]]
) -> list[ScannedModule]:
    """Attach toolkit 0.15.0 effective-parameter metadata for HTTP proxying.

    Runs each OpenAPI document through
    :meth:`apcore_toolkit.OpenAPIScanner.scan_with_effective_parameters` and
    copies the matching operation's ``input_schema`` and
    ``metadata["openapi"]`` (including ``proxy_inputs``) onto the adapter's
    scanned module. Matching uses the module's HTTP method and URL path, so
    Django-specific module IDs, targets and metadata are preserved.

    Only the ``create_cli()`` proxy path uses this: it makes path-item
    inherited parameters visible to the CLI and lets
    :func:`apcore_toolkit.validate_effective_proxy_modules` detect operations
    that cannot be forwarded losslessly.
    """
    from apcore_toolkit import OpenAPIScanner

    effective: dict[tuple[str, str], ScannedModule] = {}
    for spec in specs:
        for candidate in OpenAPIScanner().scan_with_effective_parameters(spec):
            metadata = candidate.metadata or {}
            method = str(metadata.get("http_method", "")).upper()
            path = str(metadata.get("url_path", ""))
            effective[(method, path)] = candidate

    enriched: list[ScannedModule] = []
    for module in modules:
        metadata = dict(module.metadata or {})
        raw_method = getattr(module, "http_method", "") or metadata.get(
            "http_method", ""
        )
        method = str(raw_method).upper()
        path = str(getattr(module, "url_path", "") or metadata.get("url_path", ""))
        candidate = effective.get((method, path))
        if candidate is None:
            enriched.append(module)
            continue

        openapi_meta = dict(metadata.get("openapi") or {})
        openapi_meta.update(candidate.metadata.get("openapi") or {})
        metadata["openapi"] = openapi_meta
        enriched.append(
            replace(
                module,
                input_schema=candidate.input_schema,
                metadata=metadata,
            )
        )
    return enriched

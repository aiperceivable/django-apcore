"""YAML binding file generator for Django-scanned modules.

Subclasses apcore-toolkit's ``YAMLWriter`` so the files it emits stay loadable
by apcore's runtime ``BindingLoader``. As of apcore 0.32 (PROTOCOL_SPEC
§5.12.2), a binding entry carrying a key outside the canonical binding schema
fails with ``BINDING_FILE_INVALID``. The toolkit writer always emits
``examples`` and, when set, ``suggested_alias`` / ``display`` — none of which
the core loader accepts — so those keys are dropped here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from apcore_toolkit.output.yaml_writer import YAMLWriter as ToolkitYAMLWriter

if TYPE_CHECKING:
    from apcore_toolkit.types import ScannedModule

# Keys the toolkit writer emits that apcore's BindingLoader rejects.
_DROP_KEYS = ("examples", "suggested_alias", "display")


class YAMLWriter(ToolkitYAMLWriter):
    """Generate binding files compatible with ``apcore.BindingLoader``."""

    def _build_binding(self, module: ScannedModule) -> dict[str, Any]:
        binding = super()._build_binding(module)
        for entry in binding.get("bindings", []):
            for key in _DROP_KEYS:
                entry.pop(key, None)
        return binding


__all__ = ["YAMLWriter"]

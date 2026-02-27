"""Base scanner interface and ScannedModule dataclass.

All scanners (NinjaScanner, DRFScanner) extend BaseScanner and produce
lists of ScannedModule instances.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScannedModule:
    """Result of scanning a single endpoint.

    Attributes:
        module_id: Unique module identifier (e.g., 'api.v1.users.list').
        description: Human-readable description for MCP tool listing.
        input_schema: JSON Schema dict for module input.
        output_schema: JSON Schema dict for module output.
        tags: Categorization tags.
        target: Callable reference in 'module.path:callable' format.
        version: Module version string.
        warnings: Non-fatal issues encountered during scanning.
    """

    module_id: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    tags: list[str]
    target: str
    version: str = "1.0.0"
    warnings: list[str] = field(default_factory=list)
    annotations: dict[str, bool] | None = field(default=None)


class BaseScanner(ABC):
    """Abstract base class for all scanners.

    Subclasses must implement scan() and get_source_name().
    The filter_modules() utility is provided for include/exclude filtering.
    """

    @abstractmethod
    def scan(
        self,
        include: str | None = None,
        exclude: str | None = None,
    ) -> list[ScannedModule]:
        """Scan endpoints and return module definitions.

        Args:
            include: Regex pattern to include (matches against module_id).
            exclude: Regex pattern to exclude (matches against module_id).

        Returns:
            List of ScannedModule instances.
        """
        ...

    @abstractmethod
    def get_source_name(self) -> str:
        """Return human-readable scanner name (e.g., 'django-ninja')."""
        ...

    def filter_modules(
        self,
        modules: list[ScannedModule],
        include: str | None = None,
        exclude: str | None = None,
    ) -> list[ScannedModule]:
        """Apply include/exclude regex filters to a list of ScannedModules.

        Args:
            modules: List of ScannedModule instances to filter.
            include: If set, only modules whose module_id matches are kept.
            exclude: If set, modules whose module_id matches are removed.

        Returns:
            Filtered list of ScannedModule instances.
        """
        result = modules

        if include is not None:
            pattern = re.compile(include)
            result = [m for m in result if pattern.search(m.module_id)]

        if exclude is not None:
            pattern = re.compile(exclude)
            result = [m for m in result if not pattern.search(m.module_id)]

        return result

    def _deduplicate_ids(self, ids: list[str]) -> list[str]:
        """Resolve duplicate module IDs per BL-003.

        Appends _2, _3, etc. to duplicates.
        """
        seen: dict[str, int] = {}
        result: list[str] = []
        for id_ in ids:
            if id_ in seen:
                seen[id_] += 1
                result.append(f"{id_}_{seen[id_]}")
            else:
                seen[id_] = 1
                result.append(id_)
        return result

    @staticmethod
    def _resolve_ref(ref_string: str, openapi_doc: dict[str, Any]) -> dict[str, Any]:
        """Resolve a JSON $ref pointer like '#/components/schemas/Foo'."""
        if not ref_string.startswith("#/"):
            return {}
        parts = ref_string[2:].split("/")
        current: Any = openapi_doc
        for part in parts:
            if not isinstance(current, dict):
                return {}
            current = current.get(part, {})
        return current if isinstance(current, dict) else {}

    @staticmethod
    def _resolve_schema(
        schema: dict[str, Any],
        openapi_doc: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """If schema is a $ref, resolve it; otherwise return as-is."""
        if openapi_doc and "$ref" in schema:
            return BaseScanner._resolve_ref(schema["$ref"], openapi_doc)
        return schema

    def _extract_input_schema(
        self,
        operation: dict[str, Any],
        openapi_doc: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Extract input schema from an OpenAPI operation."""
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        # Query/path parameters
        for param in operation.get("parameters", []):
            if param.get("in") in ("query", "path"):
                name = param["name"]
                param_schema = param.get("schema", {"type": "string"})
                param_schema = self._resolve_schema(param_schema, openapi_doc)
                schema["properties"][name] = param_schema
                if param.get("required", False):
                    schema["required"].append(name)

        # Request body
        request_body = operation.get("requestBody", {})
        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        body_schema = json_content.get("schema", {})
        if body_schema:
            body_schema = self._resolve_schema(body_schema, openapi_doc)
            schema["properties"].update(body_schema.get("properties", {}))
            schema["required"].extend(body_schema.get("required", []))

        return schema

    def _extract_output_schema(
        self,
        operation: dict[str, Any],
        openapi_doc: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Extract output schema from OpenAPI operation responses (200/201)."""
        responses = operation.get("responses", {})
        for status_code in ("200", "201"):
            response = responses.get(status_code, {})
            content = response.get("content", {})
            json_content = content.get("application/json", {})
            if "schema" in json_content:
                schema: dict[str, Any] = json_content["schema"]
                schema = self._resolve_schema(schema, openapi_doc)
                # Handle array with $ref items
                if schema.get("type") == "array" and "$ref" in schema.get("items", {}):
                    schema["items"] = self._resolve_schema(
                        schema["items"],
                        openapi_doc,
                    )
                return schema

        return {"type": "object", "properties": {}}

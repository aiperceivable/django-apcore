"""DRFScanner: scans DRF ViewSets via drf-spectacular OpenAPI generation.

Requires drf-spectacular >= 0.27 (optional dependency).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from django_apcore.scanners.base import BaseScanner, ScannedModule

logger = logging.getLogger("django_apcore")


class DRFScanner(BaseScanner):
    """Scanner for Django REST Framework endpoints.

    Uses drf-spectacular's SchemaGenerator to produce an OpenAPI 3.0 document,
    then iterates over operations to extract schemas.
    """

    def get_source_name(self) -> str:
        return "drf-spectacular"

    def scan(
        self,
        include: str | None = None,
        exclude: str | None = None,
    ) -> list[ScannedModule]:
        """Scan all DRF endpoints via drf-spectacular.

        Args:
            include: Regex pattern to include (matches against module_id).
            exclude: Regex pattern to exclude.

        Returns:
            List of ScannedModule instances.

        Raises:
            ImportError: If drf-spectacular is not installed.
        """
        self._check_drf_installed()
        schema = self._get_openapi_schema()
        modules = self._schema_to_modules(schema)
        return self.filter_modules(modules, include, exclude)

    def _check_drf_installed(self) -> None:
        """Verify drf-spectacular is available."""
        try:
            import drf_spectacular  # noqa: F401
        except ImportError as err:
            raise ImportError(
                "drf-spectacular is required for --source drf. "
                "Install with: pip install django-apcore[drf]"
            ) from err

    def _get_openapi_schema(self) -> dict[str, Any]:
        """Generate OpenAPI 3.0 schema via drf-spectacular."""
        from drf_spectacular.generators import SchemaGenerator

        generator = SchemaGenerator()
        schema: dict[str, Any] = generator.get_schema()
        return schema

    def _schema_to_modules(self, schema: dict[str, Any]) -> list[ScannedModule]:
        """Convert OpenAPI schema to list of ScannedModules."""
        modules = []
        paths = schema.get("paths", {})

        for path, methods in paths.items():
            for method, operation in methods.items():
                if not isinstance(operation, dict):
                    continue
                if method.lower() not in ("get", "post", "put", "patch", "delete"):
                    continue

                module = self._operation_to_module(path, method, operation, schema)
                if module:
                    modules.append(module)

        # Deduplicate IDs
        if modules:
            deduped_ids = self._deduplicate_ids([m.module_id for m in modules])
            for i, module in enumerate(modules):
                if module.module_id != deduped_ids[i]:
                    modules[i] = ScannedModule(
                        module_id=deduped_ids[i],
                        description=module.description,
                        input_schema=module.input_schema,
                        output_schema=module.output_schema,
                        tags=module.tags,
                        target=module.target,
                        version=module.version,
                        warnings=module.warnings
                        + [
                            f"Module ID renamed from '{module.module_id}' "
                            f"to '{deduped_ids[i]}' to avoid collision"
                        ],
                    )

        return modules

    def _operation_to_module(
        self,
        path: str,
        method: str,
        operation: dict[str, Any],
        openapi_doc: dict[str, Any] | None = None,
    ) -> ScannedModule | None:
        """Convert a single OpenAPI operation to a ScannedModule."""
        try:
            operation_id = operation.get("operationId")
            module_id = self._generate_module_id(path, method, operation_id)

            description = self._extract_description(
                description=operation.get("description"),
                summary=operation.get("summary"),
                operation_id=operation_id or module_id,
            )

            input_schema = self._extract_input_schema(operation, openapi_doc)
            output_schema = self._extract_output_schema(operation, openapi_doc)
            tags = operation.get("tags", [])

            # Target must be in "module.path:callable" format for PythonWriter
            target = f"{module_id}:{operation_id or module_id}"

            warnings: list[str] = []
            if not operation.get("description") and not operation.get("summary"):
                warnings.append(
                    f"Endpoint '{method.upper()} {path}' has no description"
                )

            return ScannedModule(
                module_id=module_id,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                tags=tags,
                target=target,
                warnings=warnings,
            )
        except Exception:
            logger.warning(
                "Failed to scan endpoint %s %s",
                method.upper(),
                path,
                exc_info=True,
            )
            return None

    def _generate_module_id(
        self, path: str, method: str, operation_id: str | None
    ) -> str:
        """Generate module ID per BL-002.

        If operation_id is available (from drf-spectacular), derive from it.
        Otherwise, use path + method.
        """
        if operation_id:
            # drf-spectacular generates IDs like "users_list", "users_create"
            # Convert to dotted format: "users.list"
            module_id = operation_id.replace("_", ".")
            return module_id.lower()

        # Fallback: use path segments
        cleaned = path.strip("/")
        # Remove common API prefixes
        cleaned = re.sub(r"^api/v?\d*/", "", cleaned)
        # Remove path parameters
        cleaned = re.sub(r"\{[^}]+\}", "", cleaned)
        # Convert to dots
        cleaned = re.sub(r"[^a-zA-Z0-9]+", ".", cleaned).strip(".")
        return f"{cleaned}.{method}".lower()

    def _extract_description(
        self,
        description: str | None,
        summary: str | None,
        operation_id: str,
    ) -> str:
        """Extract description per BL-005 priority chain."""
        if description:
            return description
        if summary:
            return summary
        return f"No description available for {operation_id}"

    # _extract_input_schema, _extract_output_schema, and _deduplicate_ids
    # are inherited from BaseScanner.

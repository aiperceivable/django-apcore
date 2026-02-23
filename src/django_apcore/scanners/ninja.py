"""NinjaScanner: scans django-ninja API instances for endpoint metadata.

Requires django-ninja >= 1.0 (optional dependency).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from django_apcore.scanners.base import BaseScanner, ScannedModule

logger = logging.getLogger("django_apcore")


class NinjaScanner(BaseScanner):
    """Scanner for django-ninja API endpoints.

    Discovers NinjaAPI instances from Django URL patterns, extracts
    Pydantic input/output schemas, and produces ScannedModule instances.
    """

    def get_source_name(self) -> str:
        return "django-ninja"

    def scan(
        self,
        include: str | None = None,
        exclude: str | None = None,
    ) -> list[ScannedModule]:
        """Scan all django-ninja endpoints.

        Args:
            include: Regex pattern to include (matches against module_id).
            exclude: Regex pattern to exclude.

        Returns:
            List of ScannedModule instances.

        Raises:
            ImportError: If django-ninja is not installed.
        """
        self._check_ninja_installed()
        modules = self._scan_all_endpoints()
        return self.filter_modules(modules, include, exclude)

    def _check_ninja_installed(self) -> None:
        """Verify django-ninja is available."""
        try:
            import ninja  # noqa: F401
        except ImportError:
            raise ImportError(
                "django-ninja is required for --source ninja. "
                "Install with: pip install django-apcore[ninja]"
            ) from None

    def _discover_ninja_apis(self) -> list[Any]:
        """Discover all NinjaAPI instances from Django URL patterns."""
        from django.urls import get_resolver

        apis: list[Any] = []
        try:
            from ninja import NinjaAPI

            resolver = get_resolver()
            self._find_apis(resolver.url_patterns, apis, NinjaAPI)
        except ImportError:
            pass
        return apis

    def _find_apis(self, patterns: Any, apis: list[Any], api_class: type) -> None:
        """Recursively search URL patterns for NinjaAPI instances."""
        for pattern in patterns:
            if hasattr(pattern, "callback") and isinstance(
                getattr(pattern.callback, "api", None), api_class
            ):
                api = pattern.callback.api
                if api not in apis:
                    apis.append(api)
            if hasattr(pattern, "url_patterns"):
                self._find_apis(pattern.url_patterns, apis, api_class)

    def _scan_all_endpoints(self) -> list[ScannedModule]:
        """Scan all discovered NinjaAPI instances."""
        apis = self._discover_ninja_apis()
        modules: list[ScannedModule] = []

        for api in apis:
            api_prefix = getattr(api, "urls_namespace", "") or ""
            try:
                schema = api.get_openapi_schema()
                paths = schema.get("paths", {})

                for path, methods in paths.items():
                    for method, operation in methods.items():
                        if method.lower() in (
                            "get",
                            "post",
                            "put",
                            "patch",
                            "delete",
                        ):
                            module = self._operation_to_module(
                                api, api_prefix, path, method, operation
                            )
                            if module:
                                modules.append(module)
            except Exception:
                logger.warning("Error scanning NinjaAPI instance", exc_info=True)

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
                        warnings=[
                            *module.warnings,
                            f"Module ID renamed from '{module.module_id}' "
                            f"to '{deduped_ids[i]}' to avoid collision",
                        ],
                    )

        return modules

    def _operation_to_module(
        self,
        api: Any,
        api_prefix: str,
        path: str,
        method: str,
        operation: dict[str, Any],
    ) -> ScannedModule | None:
        """Convert an OpenAPI operation to a ScannedModule."""
        try:
            module_id = self._generate_module_id(api_prefix, path, method)
            operation_id = operation.get("operationId", module_id)

            description = self._extract_description(
                description=operation.get("description"),
                docstring=operation.get("summary"),
                operation_id=operation_id,
            )

            input_schema = self._extract_input_schema(operation)
            output_schema = self._extract_output_schema(operation)

            tags = operation.get("tags", [])
            target = f"{api.__module__}:{operation_id}"

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

    def _generate_module_id(self, api_prefix: str, path: str, method: str) -> str:
        """Generate module ID per BL-001.

        Format: {api_prefix}.{path_segments}.{method} lowercased,
        special chars replaced.
        """
        # Clean prefix and path
        combined = f"{api_prefix}/{path}".strip("/")
        # Remove path parameters (e.g., {id})
        combined = re.sub(r"\{[^}]+\}", "", combined)
        # Replace non-alphanumeric with dots
        combined = re.sub(r"[^a-zA-Z0-9]+", ".", combined)
        # Remove trailing/leading dots
        combined = combined.strip(".")
        # Append method
        module_id = f"{combined}.{method}".lower()
        # Clean up double dots
        module_id = re.sub(r"\.+", ".", module_id)
        return module_id

    def _extract_description(
        self,
        description: str | None,
        docstring: str | None,
        operation_id: str,
    ) -> str:
        """Extract description per BL-004 priority chain."""
        if description:
            return description
        if docstring:
            return docstring.split("\n")[0].strip()
        return f"No description available for {operation_id}"

    # _extract_input_schema, _extract_output_schema, and _deduplicate_ids
    # are inherited from BaseScanner.

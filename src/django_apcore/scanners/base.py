"""Base scanner interface and ScannedModule dataclass.

Re-exports from apcore-toolkit for backwards compatibility.
All scanners (NinjaScanner, DRFScanner) extend BaseScanner and produce
lists of ScannedModule instances.
"""

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
    "extract_input_schema",
    "extract_output_schema",
    "resolve_ref",
    "resolve_schema",
]

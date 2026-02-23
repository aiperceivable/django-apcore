"""Scanner subpackage.

Provides BaseScanner, ScannedModule, and scanner discovery utilities.
"""

from __future__ import annotations

from django_apcore.scanners.base import BaseScanner, ScannedModule

__all__ = ["BaseScanner", "ScannedModule"]


def get_scanner(source: str) -> BaseScanner:
    """Return a scanner instance for the given source.

    Args:
        source: Scanner source identifier ('ninja' or 'drf').

    Returns:
        A BaseScanner subclass instance.

    Raises:
        ValueError: If the source is not recognized.
        ImportError: If the required optional dependency is not installed.
    """
    if source == "ninja":
        from django_apcore.scanners.ninja import NinjaScanner

        return NinjaScanner()
    elif source == "drf":
        from django_apcore.scanners.drf import DRFScanner

        return DRFScanner()
    else:
        msg = f"Unknown scanner source: '{source}'. Must be 'ninja' or 'drf'."
        raise ValueError(msg)

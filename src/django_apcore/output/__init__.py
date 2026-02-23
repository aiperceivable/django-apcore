"""Output writer subpackage.

Provides YAMLWriter and PythonWriter for serializing ScannedModule lists.
"""

from __future__ import annotations

from django_apcore.output.python_writer import PythonWriter
from django_apcore.output.yaml_writer import YAMLWriter


def get_writer(output_format: str) -> YAMLWriter | PythonWriter:
    """Return a writer instance for the given output format.

    Args:
        output_format: Output format ('yaml' or 'python').

    Returns:
        A writer instance with a write() method.

    Raises:
        ValueError: If the format is not recognized.
    """
    if output_format == "yaml":
        return YAMLWriter()
    elif output_format == "python":
        return PythonWriter()
    else:
        raise ValueError(
            f"Unknown output format: '{output_format}'. Must be 'yaml' or 'python'."
        )

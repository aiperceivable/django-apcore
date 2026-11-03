"""Output writer subpackage.

Re-exports from apcore-toolkit. Provides YAMLWriter, PythonWriter,
RegistryWriter, DjangoRegistryWriter, and WriteResult for serializing
ScannedModule lists.
"""

from __future__ import annotations

from typing import Any

from apcore_toolkit.output import WriteResult
from apcore_toolkit.output import get_writer as _toolkit_get_writer
from apcore_toolkit.output.python_writer import PythonWriter
from apcore_toolkit.output.registry_writer import RegistryWriter

from django_apcore.output.registry_writer import DjangoRegistryWriter
from django_apcore.output.yaml_writer import YAMLWriter


def get_writer(output_format: str, **kwargs: Any) -> Any:
    """Return a writer for ``output_format``.

    The ``yaml`` format resolves to :class:`django_apcore.output.yaml_writer.YAMLWriter`
    so generated bindings omit keys apcore's strict ``BindingLoader`` rejects.
    Every other format delegates to apcore-toolkit.
    """
    if output_format == "yaml":
        if kwargs:
            raise TypeError(
                f"YAMLWriter accepts no keyword arguments, got: {sorted(kwargs)}"
            )
        return YAMLWriter()
    return _toolkit_get_writer(output_format, **kwargs)


__all__ = [
    "DjangoRegistryWriter",
    "PythonWriter",
    "RegistryWriter",
    "WriteResult",
    "YAMLWriter",
    "get_writer",
]

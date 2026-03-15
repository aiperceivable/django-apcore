"""Output writer subpackage.

Re-exports from apcore-toolkit. Provides YAMLWriter, PythonWriter,
RegistryWriter, DjangoRegistryWriter, and WriteResult for serializing
ScannedModule lists.
"""

from __future__ import annotations

from apcore_toolkit.output import WriteResult, get_writer
from apcore_toolkit.output.python_writer import PythonWriter
from apcore_toolkit.output.registry_writer import RegistryWriter
from apcore_toolkit.output.yaml_writer import YAMLWriter

from django_apcore.output.registry_writer import DjangoRegistryWriter

__all__ = [
    "DjangoRegistryWriter",
    "PythonWriter",
    "RegistryWriter",
    "WriteResult",
    "YAMLWriter",
    "get_writer",
]

"""Re-export all @module-decorated functions for apcore auto-discovery.

DjangoDiscoverer scans dir() of this module, so all decorated functions
must be importable from here.
"""

from demo.apcore_modules.task_stats import task_stats

__all__ = ["task_stats"]

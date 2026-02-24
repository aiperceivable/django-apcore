"""Re-export all @module-decorated functions for apcore auto-discovery.

DjangoDiscoverer scans dir() of this module, so all decorated functions
must be importable from here.
"""

from demo.apcore_modules.hello import hello_world
from demo.apcore_modules.math_tools import add, multiply
from demo.apcore_modules.slow_task import slow_process

__all__ = ["hello_world", "add", "multiply", "slow_process"]

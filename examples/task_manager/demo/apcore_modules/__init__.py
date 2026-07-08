"""apcore modules for the demo project.

Modules registered via ``@app.module()`` (DjangoApcore) are self-registering
at import time — they do NOT need to be re-exported here for auto-discovery.

This file imports the module file to ensure the decorator runs during
Django startup, but does NOT re-export the decorated function to avoid
duplicate registration by DjangoDiscoverer.
"""

import demo.apcore_modules.task_stats  # noqa: F401

#!/usr/bin/env python
"""Entry point for the django-apcore ACL demo.

python examples/acl_demo/manage.py runserver
"""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "examples.acl_demo.settings")
    # Put the repo root on sys.path so `examples.acl_demo.*` resolves.
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

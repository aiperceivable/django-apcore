#!/bin/bash
set -e

echo "=== Scanning django-ninja routes ==="
python manage.py apcore_scan --source ninja --output yaml --dir ./demo/apcore_modules

echo ""
echo "=== Starting MCP server on port 9090 ==="
python manage.py apcore_serve --transport streamable-http --host 0.0.0.0 --port 9090 --validate-inputs --log-level DEBUG

FROM python:3.11-slim

WORKDIR /app

# Copy the entire repo (needed for pip install -e .[all])
COPY . .

# Install django-apcore in editable mode with all extras
RUN pip install --no-cache-dir -e ".[all]"

WORKDIR /app/example

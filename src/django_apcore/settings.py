"""APCORE_* settings resolution and validation.

Reads all APCORE_* settings from django.conf.settings, applies defaults,
validates types and values, and exposes a frozen dataclass for internal use.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Defaults
DEFAULT_MODULE_DIR = "apcore_modules/"
DEFAULT_AUTO_DISCOVER = True
DEFAULT_SERVE_TRANSPORT = "stdio"
DEFAULT_SERVE_HOST = "127.0.0.1"
DEFAULT_SERVE_PORT = 8000
DEFAULT_SERVER_NAME = "apcore-mcp"
DEFAULT_BINDING_PATTERN = "*.binding.yaml"

VALID_TRANSPORTS = ("stdio", "streamable-http", "sse")
VALID_SAMPLING_STRATEGIES = ("full", "proportional", "error_first", "off")


@dataclass(frozen=True)
class ApcoreSettings:
    """Validated APCORE_* settings."""

    module_dir: str
    auto_discover: bool
    serve_transport: str
    serve_host: str
    serve_port: int
    server_name: str
    binding_pattern: str
    middlewares: list[str]
    acl_path: str | None
    context_factory: str | None
    server_version: str | None
    executor_config: dict | None
    validate_inputs: bool
    observability_logging: bool | dict | None
    tracing: bool | dict | None
    metrics: bool | dict | None
    embedded_server: bool | dict | None


def get_apcore_settings() -> ApcoreSettings:
    """Read and validate APCORE_* settings from django.conf.settings.

    Returns:
        Validated ApcoreSettings dataclass.

    Raises:
        ImproperlyConfigured: If any setting is invalid.
    """
    # Read with defaults (None means "use default")
    module_dir = getattr(settings, "APCORE_MODULE_DIR", DEFAULT_MODULE_DIR)
    if module_dir is None:
        module_dir = DEFAULT_MODULE_DIR
    if not isinstance(module_dir, str | Path):
        actual = type(module_dir).__name__
        raise ImproperlyConfigured(
            "APCORE_MODULE_DIR must be a string path." f" Got: {actual}"
        )
    module_dir = str(module_dir)

    auto_discover = getattr(settings, "APCORE_AUTO_DISCOVER", DEFAULT_AUTO_DISCOVER)
    if auto_discover is None:
        auto_discover = DEFAULT_AUTO_DISCOVER
    if not isinstance(auto_discover, bool):
        actual = type(auto_discover).__name__
        raise ImproperlyConfigured(
            "APCORE_AUTO_DISCOVER must be a boolean." f" Got: {actual}"
        )

    serve_transport = getattr(
        settings,
        "APCORE_SERVE_TRANSPORT",
        DEFAULT_SERVE_TRANSPORT,
    )
    if serve_transport is None:
        serve_transport = DEFAULT_SERVE_TRANSPORT
    if serve_transport not in VALID_TRANSPORTS:
        choices = ", ".join(VALID_TRANSPORTS)
        raise ImproperlyConfigured(
            "APCORE_SERVE_TRANSPORT must be one of:"
            f" {choices}. Got: '{serve_transport}'"
        )

    serve_host = getattr(settings, "APCORE_SERVE_HOST", DEFAULT_SERVE_HOST)
    if serve_host is None:
        serve_host = DEFAULT_SERVE_HOST
    if not isinstance(serve_host, str):
        actual = type(serve_host).__name__
        raise ImproperlyConfigured(
            "APCORE_SERVE_HOST must be a valid hostname" f" or IP. Got: {actual}"
        )

    serve_port = getattr(settings, "APCORE_SERVE_PORT", DEFAULT_SERVE_PORT)
    if serve_port is None:
        serve_port = DEFAULT_SERVE_PORT
    if not isinstance(serve_port, int) or isinstance(serve_port, bool):
        actual = type(serve_port).__name__
        raise ImproperlyConfigured(
            "APCORE_SERVE_PORT must be an integer"
            f" between 1 and 65535. Got: {actual}"
        )
    if not (1 <= serve_port <= 65535):
        raise ImproperlyConfigured(
            "APCORE_SERVE_PORT must be an integer"
            f" between 1 and 65535. Got: {serve_port}"
        )

    server_name = getattr(settings, "APCORE_SERVER_NAME", DEFAULT_SERVER_NAME)
    if server_name is None:
        server_name = DEFAULT_SERVER_NAME
    if (
        not isinstance(server_name, str)
        or len(server_name) == 0
        or len(server_name) > 100
    ):
        raise ImproperlyConfigured(
            "APCORE_SERVER_NAME must be a non-empty" " string up to 100 characters."
        )

    binding_pattern = getattr(
        settings,
        "APCORE_BINDING_PATTERN",
        DEFAULT_BINDING_PATTERN,
    )
    if binding_pattern is None:
        binding_pattern = DEFAULT_BINDING_PATTERN
    if not isinstance(binding_pattern, str):
        raise ImproperlyConfigured(
            "APCORE_BINDING_PATTERN must be a valid" " glob pattern string."
        )

    middlewares = getattr(settings, "APCORE_MIDDLEWARES", [])
    if middlewares is None:
        middlewares = []
    if not isinstance(middlewares, list) or not all(
        isinstance(m, str) for m in middlewares
    ):
        raise ImproperlyConfigured(
            "APCORE_MIDDLEWARES must be a list of" " dotted path strings."
        )

    acl_path = getattr(settings, "APCORE_ACL_PATH", None)
    if acl_path is not None and not isinstance(acl_path, str):
        actual = type(acl_path).__name__
        raise ImproperlyConfigured(
            "APCORE_ACL_PATH must be a string path." f" Got: {actual}"
        )

    context_factory = getattr(settings, "APCORE_CONTEXT_FACTORY", None)
    if context_factory is not None and not isinstance(context_factory, str):
        actual = type(context_factory).__name__
        raise ImproperlyConfigured(
            "APCORE_CONTEXT_FACTORY must be a string" f" dotted path. Got: {actual}"
        )

    server_version = getattr(settings, "APCORE_SERVER_VERSION", None)
    if server_version is not None and (
        not isinstance(server_version, str) or len(server_version) == 0
    ):
        raise ImproperlyConfigured(
            "APCORE_SERVER_VERSION must be a" " non-empty string if set."
        )

    executor_config = getattr(settings, "APCORE_EXECUTOR_CONFIG", None)
    if executor_config is not None and not isinstance(executor_config, dict):
        actual = type(executor_config).__name__
        raise ImproperlyConfigured(
            "APCORE_EXECUTOR_CONFIG must be a dict." f" Got: {actual}"
        )

    validate_inputs = getattr(settings, "APCORE_VALIDATE_INPUTS", False)
    if validate_inputs is None:
        validate_inputs = False
    if not isinstance(validate_inputs, bool):
        actual = type(validate_inputs).__name__
        raise ImproperlyConfigured(
            "APCORE_VALIDATE_INPUTS must be a boolean." f" Got: {actual}"
        )

    observability_logging = getattr(settings, "APCORE_OBSERVABILITY_LOGGING", None)
    if observability_logging is not None:
        if not isinstance(observability_logging, bool | dict):
            actual = type(observability_logging).__name__
            raise ImproperlyConfigured(
                "APCORE_OBSERVABILITY_LOGGING must be a" f" bool or dict. Got: {actual}"
            )
        if isinstance(observability_logging, dict):
            _validate_observability_logging_dict(observability_logging)

    tracing = getattr(settings, "APCORE_TRACING", None)
    if tracing is not None:
        if not isinstance(tracing, bool | dict):
            actual = type(tracing).__name__
            raise ImproperlyConfigured(
                "APCORE_TRACING must be a bool or dict." f" Got: {actual}"
            )
        if isinstance(tracing, dict):
            _validate_tracing_dict(tracing)

    metrics = getattr(settings, "APCORE_METRICS", None)
    if metrics is not None:
        if not isinstance(metrics, bool | dict):
            actual = type(metrics).__name__
            raise ImproperlyConfigured(
                "APCORE_METRICS must be a bool or dict." f" Got: {actual}"
            )
        if isinstance(metrics, dict):
            _validate_metrics_dict(metrics)

    embedded_server = getattr(settings, "APCORE_EMBEDDED_SERVER", None)
    if embedded_server is not None:
        if not isinstance(embedded_server, bool | dict):
            actual = type(embedded_server).__name__
            raise ImproperlyConfigured(
                "APCORE_EMBEDDED_SERVER must be a bool or" f" dict. Got: {actual}"
            )
        if isinstance(embedded_server, dict):
            _validate_embedded_server_dict(embedded_server)

    return ApcoreSettings(
        module_dir=module_dir,
        auto_discover=auto_discover,
        serve_transport=serve_transport,
        serve_host=serve_host,
        serve_port=serve_port,
        server_name=server_name,
        binding_pattern=binding_pattern,
        middlewares=middlewares,
        acl_path=acl_path,
        context_factory=context_factory,
        server_version=server_version,
        executor_config=executor_config,
        validate_inputs=validate_inputs,
        observability_logging=observability_logging,
        tracing=tracing,
        metrics=metrics,
        embedded_server=embedded_server,
    )


VALID_LOG_LEVELS = ("trace", "debug", "info", "warn", "error", "fatal")
VALID_LOG_FORMATS = ("json",)


def _validate_observability_logging_dict(config: dict) -> None:
    """Validate APCORE_OBSERVABILITY_LOGGING dict keys."""
    if "log_inputs" in config and not isinstance(config["log_inputs"], bool):
        actual = type(config["log_inputs"]).__name__
        raise ImproperlyConfigured(
            "APCORE_OBSERVABILITY_LOGGING 'log_inputs'"
            f" must be a bool. Got: {actual}"
        )
    if "log_outputs" in config and not isinstance(config["log_outputs"], bool):
        actual = type(config["log_outputs"]).__name__
        raise ImproperlyConfigured(
            "APCORE_OBSERVABILITY_LOGGING 'log_outputs'"
            f" must be a bool. Got: {actual}"
        )
    if "level" in config:
        level = config["level"]
        if level not in VALID_LOG_LEVELS:
            choices = ", ".join(VALID_LOG_LEVELS)
            raise ImproperlyConfigured(
                "APCORE_OBSERVABILITY_LOGGING 'level'"
                f" must be one of: {choices}."
                f" Got: '{level}'"
            )
    if "format" in config:
        fmt = config["format"]
        if fmt not in VALID_LOG_FORMATS:
            choices = ", ".join(VALID_LOG_FORMATS)
            raise ImproperlyConfigured(
                "APCORE_OBSERVABILITY_LOGGING 'format'"
                f" must be one of: {choices}."
                f" Got: '{fmt}'"
            )
    if "redact_sensitive" in config and not isinstance(
        config["redact_sensitive"], bool
    ):
        actual = type(config["redact_sensitive"]).__name__
        raise ImproperlyConfigured(
            "APCORE_OBSERVABILITY_LOGGING"
            " 'redact_sensitive' must be a bool."
            f" Got: {actual}"
        )


def _validate_tracing_dict(config: dict) -> None:
    """Validate APCORE_TRACING dict keys."""
    if "exporter" in config and not isinstance(config["exporter"], str):
        actual = type(config["exporter"]).__name__
        raise ImproperlyConfigured(
            "APCORE_TRACING 'exporter' must be a string." f" Got: {actual}"
        )
    if "sampling_rate" in config:
        rate = config["sampling_rate"]
        if not isinstance(rate, int | float) or isinstance(rate, bool):
            actual = type(rate).__name__
            raise ImproperlyConfigured(
                "APCORE_TRACING 'sampling_rate' must be a" f" number. Got: {actual}"
            )
        if not (0.0 <= rate <= 1.0):
            raise ImproperlyConfigured(
                "APCORE_TRACING 'sampling_rate' must be"
                f" between 0.0 and 1.0. Got: {rate}"
            )
    if "sampling_strategy" in config:
        strategy = config["sampling_strategy"]
        if strategy not in VALID_SAMPLING_STRATEGIES:
            choices = ", ".join(VALID_SAMPLING_STRATEGIES)
            raise ImproperlyConfigured(
                "APCORE_TRACING 'sampling_strategy' must"
                f" be one of: {choices}."
                f" Got: '{strategy}'"
            )
    if "otlp_endpoint" in config and not isinstance(config["otlp_endpoint"], str):
        actual = type(config["otlp_endpoint"]).__name__
        raise ImproperlyConfigured(
            "APCORE_TRACING 'otlp_endpoint' must be a" f" string. Got: {actual}"
        )
    if "otlp_service_name" in config and not isinstance(
        config["otlp_service_name"], str
    ):
        actual = type(config["otlp_service_name"]).__name__
        raise ImproperlyConfigured(
            "APCORE_TRACING 'otlp_service_name' must be a" f" string. Got: {actual}"
        )


def _validate_metrics_dict(config: dict) -> None:
    """Validate APCORE_METRICS dict keys."""
    if "buckets" in config:
        buckets = config["buckets"]
        if not isinstance(buckets, list):
            actual = type(buckets).__name__
            raise ImproperlyConfigured(
                "APCORE_METRICS 'buckets' must be a list." f" Got: {actual}"
            )
        if not all(
            isinstance(b, int | float) and not isinstance(b, bool) for b in buckets
        ):
            raise ImproperlyConfigured(
                "APCORE_METRICS 'buckets' must contain" " only numbers."
            )


def _validate_embedded_server_dict(config: dict) -> None:
    """Validate APCORE_EMBEDDED_SERVER dict keys."""
    if "transport" in config and config["transport"] not in VALID_TRANSPORTS:
        choices = ", ".join(VALID_TRANSPORTS)
        raise ImproperlyConfigured(
            "APCORE_EMBEDDED_SERVER 'transport' must"
            f" be one of: {choices}."
            f" Got: '{config['transport']}'"
        )
    if "host" in config and not isinstance(config["host"], str):
        actual = type(config["host"]).__name__
        raise ImproperlyConfigured(
            "APCORE_EMBEDDED_SERVER 'host' must be a" f" string. Got: {actual}"
        )
    if "port" in config:
        port = config["port"]
        if not isinstance(port, int) or isinstance(port, bool):
            actual = type(port).__name__
            raise ImproperlyConfigured(
                "APCORE_EMBEDDED_SERVER 'port' must be an" f" integer. Got: {actual}"
            )
        if not (1 <= port <= 65535):
            raise ImproperlyConfigured(
                "APCORE_EMBEDDED_SERVER 'port' must be"
                f" between 1 and 65535. Got: {port}"
            )
    if "name" in config:
        name = config["name"]
        if not isinstance(name, str) or len(name) == 0 or len(name) > 100:
            raise ImproperlyConfigured(
                "APCORE_EMBEDDED_SERVER 'name' must be a"
                " non-empty string up to 100 characters."
            )
    if "version" in config and not isinstance(config["version"], str):
        actual = type(config["version"]).__name__
        raise ImproperlyConfigured(
            "APCORE_EMBEDDED_SERVER 'version' must be a" f" string. Got: {actual}"
        )

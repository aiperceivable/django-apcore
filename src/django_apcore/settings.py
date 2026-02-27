"""APCORE_* settings resolution and validation.

Reads all APCORE_* settings from django.conf.settings, applies defaults,
validates types and values, and exposes a frozen dataclass for internal use.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

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

DEFAULT_EXPLORER_ENABLED = False
DEFAULT_EXPLORER_PREFIX = "/explorer"
DEFAULT_EXPLORER_ALLOW_EXECUTE = False

DEFAULT_TASK_MAX_CONCURRENT = 10
DEFAULT_TASK_MAX_TASKS = 1000
DEFAULT_TASK_CLEANUP_AGE = 3600
VALID_SERVE_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


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
    executor_config: dict[str, Any] | None
    validate_inputs: bool
    observability_logging: bool | dict[str, Any] | None
    tracing: bool | dict[str, Any] | None
    metrics: bool | dict[str, Any] | None
    embedded_server: bool | dict[str, Any] | None
    extensions_dir: str | None
    module_validators: list[str]
    task_max_concurrent: int
    task_max_tasks: int
    task_cleanup_age: int
    cancel_default_timeout: int | None
    serve_validate_inputs: bool
    serve_metrics: bool
    serve_log_level: str | None
    serve_tags: list[str] | None
    serve_prefix: str | None
    explorer_enabled: bool
    explorer_prefix: str
    explorer_allow_execute: bool
    hot_reload: bool
    hot_reload_paths: list[str]


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

    # --- v0.1.0 settings ---

    extensions_dir = getattr(settings, "APCORE_EXTENSIONS_DIR", None)
    if extensions_dir is not None and not isinstance(extensions_dir, str):
        actual = type(extensions_dir).__name__
        raise ImproperlyConfigured(
            "APCORE_EXTENSIONS_DIR must be a string path." f" Got: {actual}"
        )

    module_validators = getattr(settings, "APCORE_MODULE_VALIDATORS", [])
    if module_validators is None:
        module_validators = []
    if not isinstance(module_validators, list) or not all(
        isinstance(v, str) for v in module_validators
    ):
        raise ImproperlyConfigured(
            "APCORE_MODULE_VALIDATORS must be a list of" " dotted path strings."
        )

    task_max_concurrent = getattr(
        settings,
        "APCORE_TASK_MAX_CONCURRENT",
        DEFAULT_TASK_MAX_CONCURRENT,
    )
    if task_max_concurrent is None:
        task_max_concurrent = DEFAULT_TASK_MAX_CONCURRENT
    if not isinstance(task_max_concurrent, int) or isinstance(
        task_max_concurrent, bool
    ):
        actual = type(task_max_concurrent).__name__
        raise ImproperlyConfigured(
            "APCORE_TASK_MAX_CONCURRENT must be a positive" f" integer. Got: {actual}"
        )
    if task_max_concurrent < 1:
        raise ImproperlyConfigured(
            "APCORE_TASK_MAX_CONCURRENT must be a positive"
            f" integer. Got: {task_max_concurrent}"
        )

    task_max_tasks = getattr(
        settings,
        "APCORE_TASK_MAX_TASKS",
        DEFAULT_TASK_MAX_TASKS,
    )
    if task_max_tasks is None:
        task_max_tasks = DEFAULT_TASK_MAX_TASKS
    if not isinstance(task_max_tasks, int) or isinstance(task_max_tasks, bool):
        actual = type(task_max_tasks).__name__
        raise ImproperlyConfigured(
            "APCORE_TASK_MAX_TASKS must be a positive" f" integer. Got: {actual}"
        )
    if task_max_tasks < 1:
        raise ImproperlyConfigured(
            "APCORE_TASK_MAX_TASKS must be a positive"
            f" integer. Got: {task_max_tasks}"
        )

    task_cleanup_age = getattr(
        settings,
        "APCORE_TASK_CLEANUP_AGE",
        DEFAULT_TASK_CLEANUP_AGE,
    )
    if task_cleanup_age is None:
        task_cleanup_age = DEFAULT_TASK_CLEANUP_AGE
    if not isinstance(task_cleanup_age, int) or isinstance(task_cleanup_age, bool):
        actual = type(task_cleanup_age).__name__
        raise ImproperlyConfigured(
            "APCORE_TASK_CLEANUP_AGE must be a non-negative" f" integer. Got: {actual}"
        )
    if task_cleanup_age < 0:
        raise ImproperlyConfigured(
            "APCORE_TASK_CLEANUP_AGE must be a non-negative"
            f" integer. Got: {task_cleanup_age}"
        )

    cancel_default_timeout = getattr(
        settings,
        "APCORE_CANCEL_DEFAULT_TIMEOUT",
        None,
    )
    if cancel_default_timeout is not None:
        if not isinstance(cancel_default_timeout, int) or isinstance(
            cancel_default_timeout, bool
        ):
            actual = type(cancel_default_timeout).__name__
            raise ImproperlyConfigured(
                "APCORE_CANCEL_DEFAULT_TIMEOUT must be a"
                f" positive integer. Got: {actual}"
            )
        if cancel_default_timeout < 1:
            raise ImproperlyConfigured(
                "APCORE_CANCEL_DEFAULT_TIMEOUT must be a"
                f" positive integer. Got: {cancel_default_timeout}"
            )

    serve_validate_inputs = getattr(
        settings,
        "APCORE_SERVE_VALIDATE_INPUTS",
        False,
    )
    if serve_validate_inputs is None:
        serve_validate_inputs = False
    if not isinstance(serve_validate_inputs, bool):
        actual = type(serve_validate_inputs).__name__
        raise ImproperlyConfigured(
            "APCORE_SERVE_VALIDATE_INPUTS must be a boolean." f" Got: {actual}"
        )

    serve_metrics = getattr(settings, "APCORE_SERVE_METRICS", False)
    if serve_metrics is None:
        serve_metrics = False
    if not isinstance(serve_metrics, bool):
        actual = type(serve_metrics).__name__
        raise ImproperlyConfigured(
            "APCORE_SERVE_METRICS must be a boolean." f" Got: {actual}"
        )

    serve_log_level = getattr(settings, "APCORE_SERVE_LOG_LEVEL", None)
    if serve_log_level is not None and serve_log_level not in VALID_SERVE_LOG_LEVELS:
        choices = ", ".join(VALID_SERVE_LOG_LEVELS)
        raise ImproperlyConfigured(
            "APCORE_SERVE_LOG_LEVEL must be one of:"
            f" {choices}. Got: '{serve_log_level}'"
        )

    serve_tags = getattr(settings, "APCORE_SERVE_TAGS", None)
    if serve_tags is not None and (
        not isinstance(serve_tags, list)
        or not all(isinstance(t, str) for t in serve_tags)
    ):
        raise ImproperlyConfigured("APCORE_SERVE_TAGS must be a list of strings.")

    serve_prefix = getattr(settings, "APCORE_SERVE_PREFIX", None)
    if serve_prefix is not None and not isinstance(serve_prefix, str):
        actual = type(serve_prefix).__name__
        raise ImproperlyConfigured(
            "APCORE_SERVE_PREFIX must be a string." f" Got: {actual}"
        )

    # --- Explorer settings (apcore-mcp Tool Explorer) ---

    explorer_enabled = getattr(
        settings, "APCORE_EXPLORER_ENABLED", DEFAULT_EXPLORER_ENABLED
    )
    if explorer_enabled is None:
        explorer_enabled = DEFAULT_EXPLORER_ENABLED
    if not isinstance(explorer_enabled, bool):
        actual = type(explorer_enabled).__name__
        raise ImproperlyConfigured(
            "APCORE_EXPLORER_ENABLED must be a boolean." f" Got: {actual}"
        )

    explorer_prefix = getattr(
        settings, "APCORE_EXPLORER_PREFIX", DEFAULT_EXPLORER_PREFIX
    )
    if explorer_prefix is None:
        explorer_prefix = DEFAULT_EXPLORER_PREFIX
    if not isinstance(explorer_prefix, str) or not explorer_prefix.startswith("/"):
        raise ImproperlyConfigured(
            "APCORE_EXPLORER_PREFIX must be a string starting with '/'."
        )

    explorer_allow_execute = getattr(
        settings, "APCORE_EXPLORER_ALLOW_EXECUTE", DEFAULT_EXPLORER_ALLOW_EXECUTE
    )
    if explorer_allow_execute is None:
        explorer_allow_execute = DEFAULT_EXPLORER_ALLOW_EXECUTE
    if not isinstance(explorer_allow_execute, bool):
        actual = type(explorer_allow_execute).__name__
        raise ImproperlyConfigured(
            "APCORE_EXPLORER_ALLOW_EXECUTE must be a boolean." f" Got: {actual}"
        )

    hot_reload = getattr(settings, "APCORE_HOT_RELOAD", False)
    if hot_reload is None:
        hot_reload = False
    if not isinstance(hot_reload, bool):
        actual = type(hot_reload).__name__
        raise ImproperlyConfigured(
            "APCORE_HOT_RELOAD must be a boolean." f" Got: {actual}"
        )

    hot_reload_paths = getattr(settings, "APCORE_HOT_RELOAD_PATHS", [])
    if hot_reload_paths is None:
        hot_reload_paths = []
    if not isinstance(hot_reload_paths, list) or not all(
        isinstance(p, str) for p in hot_reload_paths
    ):
        raise ImproperlyConfigured(
            "APCORE_HOT_RELOAD_PATHS must be a list of" " string paths."
        )

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
        extensions_dir=extensions_dir,
        module_validators=module_validators,
        task_max_concurrent=task_max_concurrent,
        task_max_tasks=task_max_tasks,
        task_cleanup_age=task_cleanup_age,
        cancel_default_timeout=cancel_default_timeout,
        serve_validate_inputs=serve_validate_inputs,
        serve_metrics=serve_metrics,
        serve_log_level=serve_log_level,
        serve_tags=serve_tags,
        serve_prefix=serve_prefix,
        explorer_enabled=explorer_enabled,
        explorer_prefix=explorer_prefix,
        explorer_allow_execute=explorer_allow_execute,
        hot_reload=hot_reload,
        hot_reload_paths=hot_reload_paths,
    )


VALID_LOG_LEVELS = ("trace", "debug", "info", "warn", "error", "fatal")
VALID_LOG_FORMATS = ("json",)


def _validate_observability_logging_dict(config: dict[str, Any]) -> None:
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


def _validate_tracing_dict(config: dict[str, Any]) -> None:
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


def _validate_metrics_dict(config: dict[str, Any]) -> None:
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


def _validate_embedded_server_dict(config: dict[str, Any]) -> None:
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

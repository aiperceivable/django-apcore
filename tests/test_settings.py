# tests/test_settings.py
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings


class TestApcoreSettingsDefaults:
    """Test that all APCORE_* settings have correct defaults."""

    def test_default_module_dir(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.module_dir == "apcore_modules/"

    def test_default_auto_discover(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.auto_discover is True

    def test_default_serve_transport(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_transport == "stdio"

    def test_default_serve_host(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_host == "127.0.0.1"

    def test_default_serve_port(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_port == 8000

    def test_default_server_name(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.server_name == "apcore-mcp"

    def test_default_binding_pattern(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.binding_pattern == "*.binding.yaml"


class TestApcoreSettingsCustomValues:
    """Test that custom APCORE_* settings are read correctly."""

    @override_settings(APCORE_MODULE_DIR="custom_modules/")
    def test_custom_module_dir(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.module_dir == "custom_modules/"

    @override_settings(APCORE_AUTO_DISCOVER=False)
    def test_custom_auto_discover(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.auto_discover is False

    @override_settings(APCORE_SERVE_TRANSPORT="streamable-http")
    def test_custom_serve_transport(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_transport == "streamable-http"

    @override_settings(APCORE_SERVE_PORT=9090)
    def test_custom_serve_port(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_port == 9090


class TestApcoreSettingsValidation:
    """Test invalid APCORE_* settings raise ImproperlyConfigured."""

    @override_settings(APCORE_MODULE_DIR=123)
    def test_module_dir_must_be_string(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_MODULE_DIR must be a string path",
        ):
            get_apcore_settings()

    @override_settings(APCORE_AUTO_DISCOVER="true")
    def test_auto_discover_must_be_bool(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_AUTO_DISCOVER must be a boolean",
        ):
            get_apcore_settings()

    @override_settings(APCORE_SERVE_TRANSPORT="websocket")
    def test_serve_transport_must_be_valid_choice(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_SERVE_TRANSPORT must be one of",
        ):
            get_apcore_settings()

    @override_settings(APCORE_SERVE_PORT=99999)
    def test_serve_port_must_be_in_range(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match=("APCORE_SERVE_PORT must be an integer" " between 1 and 65535"),
        ):
            get_apcore_settings()

    @override_settings(APCORE_SERVE_PORT="8080")
    def test_serve_port_must_be_int(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_SERVE_PORT must be an integer",
        ):
            get_apcore_settings()

    @override_settings(APCORE_SERVER_NAME="")
    def test_server_name_must_be_non_empty(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match=("APCORE_SERVER_NAME must be a non-empty" " string"),
        ):
            get_apcore_settings()

    @override_settings(APCORE_SERVER_NAME="x" * 101)
    def test_server_name_max_length(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match=(
                "APCORE_SERVER_NAME must be a non-empty" " string up to 100 characters"
            ),
        ):
            get_apcore_settings()


class TestNewSettingsDefaults:
    """Test defaults for v0.2.0 settings."""

    def test_default_middlewares(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.middlewares == []

    def test_default_acl_path(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.acl_path is None

    def test_default_context_factory(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.context_factory is None

    def test_default_server_version(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.server_version is None

    def test_default_executor_config(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.executor_config is None

    def test_default_validate_inputs(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.validate_inputs is False

    def test_default_observability_logging(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.observability_logging is None


class TestNewSettingsValidation:
    """Test validation for v0.2.0 settings."""

    @override_settings(APCORE_MIDDLEWARES="not-a-list")
    def test_middlewares_must_be_list(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_MIDDLEWARES must be a list",
        ):
            get_apcore_settings()

    @override_settings(APCORE_MIDDLEWARES=[123])
    def test_middlewares_must_contain_strings(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_MIDDLEWARES must be a list",
        ):
            get_apcore_settings()

    @override_settings(APCORE_ACL_PATH=123)
    def test_acl_path_must_be_string(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_ACL_PATH must be a string",
        ):
            get_apcore_settings()

    @override_settings(APCORE_CONTEXT_FACTORY=123)
    def test_context_factory_must_be_string(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_CONTEXT_FACTORY must be a string",
        ):
            get_apcore_settings()

    @override_settings(APCORE_SERVER_VERSION="")
    def test_server_version_must_be_non_empty(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_SERVER_VERSION must be a non-empty string",
        ):
            get_apcore_settings()

    @override_settings(APCORE_SERVER_VERSION=123)
    def test_server_version_must_be_string(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_SERVER_VERSION must be a non-empty string",
        ):
            get_apcore_settings()

    @override_settings(APCORE_EXECUTOR_CONFIG="not-a-dict")
    def test_executor_config_must_be_dict(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_EXECUTOR_CONFIG must be a dict",
        ):
            get_apcore_settings()

    @override_settings(APCORE_VALIDATE_INPUTS="true")
    def test_validate_inputs_must_be_bool(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_VALIDATE_INPUTS must be a boolean",
        ):
            get_apcore_settings()

    @override_settings(APCORE_OBSERVABILITY_LOGGING="true")
    def test_observability_logging_must_be_bool_or_dict(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_OBSERVABILITY_LOGGING must be a bool or dict",
        ):
            get_apcore_settings()


class TestObservabilityLoggingSettings:
    """Test APCORE_OBSERVABILITY_LOGGING extended settings."""

    def test_default_is_none(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.observability_logging is None

    @override_settings(APCORE_OBSERVABILITY_LOGGING=True)
    def test_true_passes(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.observability_logging is True

    @override_settings(
        APCORE_OBSERVABILITY_LOGGING={
            "log_inputs": False,
            "log_outputs": True,
            "level": "debug",
            "format": "json",
            "redact_sensitive": True,
        }
    )
    def test_valid_dict_passes(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.observability_logging["log_inputs"] is False

    @override_settings(APCORE_OBSERVABILITY_LOGGING={"log_inputs": "yes"})
    def test_invalid_log_inputs_type(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="log_inputs.*must be a bool",
        ):
            get_apcore_settings()

    @override_settings(APCORE_OBSERVABILITY_LOGGING={"log_outputs": 1})
    def test_invalid_log_outputs_type(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="log_outputs.*must be a bool",
        ):
            get_apcore_settings()

    @override_settings(APCORE_OBSERVABILITY_LOGGING={"level": "verbose"})
    def test_invalid_level(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="level.*must be one of",
        ):
            get_apcore_settings()

    @override_settings(APCORE_OBSERVABILITY_LOGGING={"format": "text"})
    def test_invalid_format(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="format.*must be one of",
        ):
            get_apcore_settings()


class TestTracingSettings:
    """Test APCORE_TRACING settings."""

    def test_default_is_none(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.tracing is None

    @override_settings(APCORE_TRACING=True)
    def test_true_passes(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.tracing is True

    @override_settings(
        APCORE_TRACING={
            "exporter": "otlp",
            "sampling_rate": 0.5,
            "sampling_strategy": "proportional",
            "otlp_endpoint": "http://localhost:4318",
            "otlp_service_name": "my-app",
        }
    )
    def test_valid_dict_passes(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.tracing["exporter"] == "otlp"

    @override_settings(APCORE_TRACING="enabled")
    def test_invalid_type_raises(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_TRACING must be a bool or dict",
        ):
            get_apcore_settings()

    @override_settings(APCORE_TRACING={"sampling_rate": "fast"})
    def test_invalid_sampling_rate_type(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="sampling_rate.*must be a number",
        ):
            get_apcore_settings()

    @override_settings(APCORE_TRACING={"sampling_rate": 2.0})
    def test_invalid_sampling_rate_range(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="sampling_rate.*between 0.0 and 1.0",
        ):
            get_apcore_settings()

    @override_settings(APCORE_TRACING={"sampling_strategy": "random"})
    def test_invalid_sampling_strategy(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="sampling_strategy.*must be one of",
        ):
            get_apcore_settings()

    @override_settings(APCORE_TRACING={"exporter": 123})
    def test_invalid_exporter_type(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="exporter.*must be a string",
        ):
            get_apcore_settings()


class TestMetricsSettings:
    """Test APCORE_METRICS settings."""

    def test_default_is_none(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.metrics is None

    @override_settings(APCORE_METRICS=True)
    def test_true_passes(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.metrics is True

    @override_settings(APCORE_METRICS={"buckets": [0.01, 0.05, 0.1, 0.5, 1.0]})
    def test_valid_dict_passes(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.metrics["buckets"] == [0.01, 0.05, 0.1, 0.5, 1.0]

    @override_settings(APCORE_METRICS="enabled")
    def test_invalid_type_raises(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_METRICS must be a bool or dict",
        ):
            get_apcore_settings()

    @override_settings(APCORE_METRICS={"buckets": "not-a-list"})
    def test_invalid_buckets_type(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="buckets.*must be a list",
        ):
            get_apcore_settings()

    @override_settings(APCORE_METRICS={"buckets": [0.1, "bad", 0.5]})
    def test_invalid_buckets_items(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="buckets.*must contain only numbers",
        ):
            get_apcore_settings()


class TestEmbeddedServerSettings:
    """Test APCORE_EMBEDDED_SERVER settings."""

    def test_default_is_none(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.embedded_server is None

    @override_settings(APCORE_EMBEDDED_SERVER=True)
    def test_true_passes(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.embedded_server is True

    @override_settings(
        APCORE_EMBEDDED_SERVER={
            "transport": "streamable-http",
            "host": "127.0.0.1",
            "port": 9000,
            "name": "apcore-embedded",
            "version": "1.0.0",
        }
    )
    def test_valid_dict_passes(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.embedded_server["port"] == 9000

    @override_settings(APCORE_EMBEDDED_SERVER="enabled")
    def test_invalid_type_raises(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="APCORE_EMBEDDED_SERVER must be a bool or dict",
        ):
            get_apcore_settings()

    @override_settings(APCORE_EMBEDDED_SERVER={"transport": "websocket"})
    def test_invalid_transport(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="transport.*must be one of",
        ):
            get_apcore_settings()

    @override_settings(APCORE_EMBEDDED_SERVER={"port": 99999})
    def test_invalid_port_range(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="port.*must be between 1 and 65535",
        ):
            get_apcore_settings()

    @override_settings(APCORE_EMBEDDED_SERVER={"port": "8000"})
    def test_invalid_port_type(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(
            ImproperlyConfigured,
            match="port.*must be an integer",
        ):
            get_apcore_settings()


class TestApcoreSettingsEdgeCases:
    """Test edge cases for settings resolution."""

    @override_settings(APCORE_MODULE_DIR=None)
    def test_none_uses_default(self):
        """Explicit None values should use defaults."""
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.module_dir == "apcore_modules/"

    def test_settings_is_frozen(self):
        """ApcoreSettings should be immutable."""
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        with pytest.raises(AttributeError):
            settings.module_dir = "changed/"  # type: ignore[misc]

    @override_settings(APCORE_SERVE_TRANSPORT="sse")
    def test_sse_transport_accepted(self):
        from django_apcore.settings import get_apcore_settings

        settings = get_apcore_settings()
        assert settings.serve_transport == "sse"


class TestV030SettingsDefaults:
    """Test defaults for v0.3.0 settings."""

    def test_new_settings_defaults(self):
        """All new v0.3.0 settings have sensible defaults."""
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.extensions_dir is None
        assert s.module_validators == []
        assert s.task_max_concurrent == 10
        assert s.task_max_tasks == 1000
        assert s.task_cleanup_age == 3600
        assert s.cancel_default_timeout is None
        assert s.serve_validate_inputs is False
        assert s.serve_metrics is False
        assert s.serve_log_level is None
        assert s.serve_tags is None
        assert s.serve_prefix is None
        assert s.hot_reload is False
        assert s.hot_reload_paths == []


class TestV030SettingsValidation:
    """Test validation for v0.3.0 settings."""

    @override_settings(APCORE_TASK_MAX_CONCURRENT="not_int")
    def test_task_max_concurrent_invalid_type(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_TASK_MAX_CONCURRENT"):
            get_apcore_settings()

    @override_settings(APCORE_TASK_MAX_CONCURRENT=-1)
    def test_task_max_concurrent_negative(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_TASK_MAX_CONCURRENT"):
            get_apcore_settings()

    @override_settings(APCORE_TASK_MAX_TASKS="not_int")
    def test_task_max_tasks_invalid(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_TASK_MAX_TASKS"):
            get_apcore_settings()

    @override_settings(APCORE_TASK_CLEANUP_AGE=-1)
    def test_task_cleanup_age_negative(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_TASK_CLEANUP_AGE"):
            get_apcore_settings()

    @override_settings(APCORE_HOT_RELOAD="yes")
    def test_hot_reload_invalid(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_HOT_RELOAD"):
            get_apcore_settings()

    @override_settings(APCORE_SERVE_LOG_LEVEL="TRACE")
    def test_serve_log_level_invalid(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_SERVE_LOG_LEVEL"):
            get_apcore_settings()

    @override_settings(APCORE_MODULE_VALIDATORS="not_a_list")
    def test_module_validators_invalid(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_MODULE_VALIDATORS"):
            get_apcore_settings()

    @override_settings(APCORE_HOT_RELOAD_PATHS="not_a_list")
    def test_hot_reload_paths_invalid(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_HOT_RELOAD_PATHS"):
            get_apcore_settings()

    @override_settings(APCORE_SERVE_VALIDATE_INPUTS="true")
    def test_serve_validate_inputs_invalid(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_SERVE_VALIDATE_INPUTS"):
            get_apcore_settings()

    @override_settings(APCORE_SERVE_METRICS="true")
    def test_serve_metrics_invalid(self):
        from django_apcore.settings import get_apcore_settings

        with pytest.raises(ImproperlyConfigured, match="APCORE_SERVE_METRICS"):
            get_apcore_settings()

    @override_settings(APCORE_SERVE_LOG_LEVEL="INFO")
    def test_serve_log_level_valid(self):
        from django_apcore.settings import get_apcore_settings

        s = get_apcore_settings()
        assert s.serve_log_level == "INFO"

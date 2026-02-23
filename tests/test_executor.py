# tests/test_executor.py
from unittest.mock import MagicMock, patch

from django.test import override_settings


class TestGetExecutor:
    """Test the get_executor() singleton."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @patch("apcore.Executor")
    def test_returns_executor_instance(self, mock_executor_cls):
        """get_executor() returns an Executor."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        executor = get_executor()
        assert executor is not None
        mock_executor_cls.assert_called_once()

    @patch("apcore.Executor")
    def test_singleton_returns_same_instance(self, mock_executor_cls):
        """get_executor() returns the same instance on repeated calls."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        e1 = get_executor()
        e2 = get_executor()
        assert e1 is e2
        mock_executor_cls.assert_called_once()

    @patch("apcore.Executor")
    def test_reset_creates_new_instance(self, mock_executor_cls):
        """After _reset_executor(), a new Executor is created."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import _reset_executor, get_executor

        e1 = get_executor()
        _reset_executor()
        mock_executor_cls.return_value = MagicMock()
        e2 = get_executor()
        assert e1 is not e2

    @override_settings(APCORE_MIDDLEWARES=["tests.test_executor.FakeMiddleware"])
    @patch("apcore.Executor")
    def test_middlewares_resolved(self, mock_executor_cls):
        """Middleware dotted paths are imported and instantiated."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        call_kwargs = mock_executor_cls.call_args
        middlewares = call_kwargs.kwargs.get("middlewares", [])
        assert len(middlewares) >= 1
        assert isinstance(middlewares[0], FakeMiddleware)

    @override_settings(APCORE_ACL_PATH="/tmp/test_acl.yaml")
    @patch("apcore.ACL")
    @patch("apcore.Executor")
    def test_acl_loaded_from_path(self, mock_executor_cls, mock_acl_cls):
        """ACL is loaded when APCORE_ACL_PATH is set."""
        mock_acl_cls.load.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        mock_acl_cls.load.assert_called_once_with("/tmp/test_acl.yaml")

    @override_settings(APCORE_EXECUTOR_CONFIG={"timeout": 30})
    @patch("apcore.Config")
    @patch("apcore.Executor")
    def test_config_created_from_dict(self, mock_executor_cls, mock_config_cls):
        """Config is created when APCORE_EXECUTOR_CONFIG is set."""
        mock_config_cls.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        mock_config_cls.assert_called_once_with(data={"timeout": 30})

    @override_settings(APCORE_OBSERVABILITY_LOGGING=True)
    @patch("apcore.ObsLoggingMiddleware")
    @patch("apcore.Executor")
    def test_observability_logging_prepends_middleware(
        self, mock_executor_cls, mock_obs_cls
    ):
        """ObsLoggingMiddleware is prepended when observability_logging=True."""
        mock_obs_instance = MagicMock()
        mock_obs_cls.return_value = mock_obs_instance
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        call_kwargs = mock_executor_cls.call_args
        middlewares = call_kwargs.kwargs.get("middlewares", [])
        assert middlewares[0] is mock_obs_instance

    @override_settings(
        APCORE_OBSERVABILITY_LOGGING={
            "log_inputs": False,
            "log_outputs": False,
        }
    )
    @patch("apcore.ObsLoggingMiddleware")
    @patch("apcore.Executor")
    def test_observability_logging_dict_passes_options(
        self, mock_executor_cls, mock_obs_cls
    ):
        """Dict config passes log_inputs/log_outputs to ObsLoggingMiddleware."""
        mock_obs_instance = MagicMock()
        mock_obs_cls.return_value = mock_obs_instance
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        mock_obs_cls.assert_called_once_with(log_inputs=False, log_outputs=False)

    @override_settings(
        APCORE_OBSERVABILITY_LOGGING={
            "level": "debug",
            "format": "json",
        }
    )
    @patch("apcore.ContextLogger")
    @patch("apcore.ObsLoggingMiddleware")
    @patch("apcore.Executor")
    def test_observability_logging_dict_creates_context_logger(
        self, mock_executor_cls, mock_obs_cls, mock_logger_cls
    ):
        """Dict config with logger options creates ContextLogger."""
        mock_logger = MagicMock()
        mock_logger_cls.return_value = mock_logger
        mock_obs_cls.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        mock_logger_cls.assert_called_once_with(
            name="apcore.obs_logging",
            level="debug",
            format="json",
        )
        mock_obs_cls.assert_called_once_with(logger=mock_logger)

    @patch("apcore.Executor")
    def test_no_acl_when_not_configured(self, mock_executor_cls):
        """ACL is None when APCORE_ACL_PATH is not set."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        call_kwargs = mock_executor_cls.call_args
        acl = call_kwargs.kwargs.get("acl")
        assert acl is None

    @patch("apcore.Executor")
    def test_no_config_when_not_configured(self, mock_executor_cls):
        """Config is None when APCORE_EXECUTOR_CONFIG is not set."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        call_kwargs = mock_executor_cls.call_args
        config = call_kwargs.kwargs.get("config")
        assert config is None

    def test_reset_registry_also_resets_executor(self):
        """_reset_registry() also resets the executor singleton."""
        import django_apcore.registry as reg
        from django_apcore.registry import _reset_registry

        reg._executor = MagicMock()
        _reset_registry()
        assert reg._executor is None

    @patch("apcore.Executor")
    def test_empty_middlewares_by_default(self, mock_executor_cls):
        """With no APCORE_MIDDLEWARES, empty list is passed."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        call_kwargs = mock_executor_cls.call_args
        middlewares = call_kwargs.kwargs.get("middlewares", [])
        assert middlewares == []

    def test_resolve_middlewares_imports_class(self):
        """_resolve_middlewares imports and instantiates classes."""
        from django_apcore.registry import _resolve_middlewares

        result = _resolve_middlewares(["tests.test_executor.FakeMiddleware"])
        assert len(result) == 1
        assert isinstance(result[0], FakeMiddleware)

    def test_resolve_middlewares_empty_list(self):
        """_resolve_middlewares with empty list returns empty."""
        from django_apcore.registry import _resolve_middlewares

        result = _resolve_middlewares([])
        assert result == []


class TestTracingMiddlewareIntegration:
    """Test TracingMiddleware integration in get_executor()."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(APCORE_TRACING=True)
    @patch("apcore.observability.tracing.StdoutExporter")
    @patch("apcore.observability.tracing.TracingMiddleware")
    @patch("apcore.Executor")
    def test_tracing_true_prepends_tracing_middleware(
        self, mock_executor_cls, mock_tracing_cls, mock_exporter_cls
    ):
        """APCORE_TRACING=True prepends TracingMiddleware with StdoutExporter."""
        mock_tracing_instance = MagicMock()
        mock_tracing_cls.return_value = mock_tracing_instance
        mock_exporter_cls.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        call_kwargs = mock_executor_cls.call_args
        middlewares = call_kwargs.kwargs.get("middlewares", [])
        assert mock_tracing_instance in middlewares

    @override_settings(
        APCORE_TRACING={
            "exporter": "otlp",
            "otlp_endpoint": "http://collector:4318",
            "otlp_service_name": "test-svc",
        }
    )
    @patch("apcore.observability.tracing.OTLPExporter")
    @patch("apcore.observability.tracing.TracingMiddleware")
    @patch("apcore.Executor")
    def test_otlp_exporter_created(
        self, mock_executor_cls, mock_tracing_cls, mock_otlp_cls
    ):
        """Dict with exporter=otlp creates OTLPExporter."""
        mock_otlp_cls.return_value = MagicMock()
        mock_tracing_cls.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        mock_otlp_cls.assert_called_once_with(
            endpoint="http://collector:4318",
            service_name="test-svc",
        )

    @override_settings(APCORE_TRACING={"exporter": "in_memory"})
    @patch("apcore.observability.tracing.InMemoryExporter")
    @patch("apcore.observability.tracing.TracingMiddleware")
    @patch("apcore.Executor")
    def test_in_memory_exporter_created(
        self, mock_executor_cls, mock_tracing_cls, mock_inmem_cls
    ):
        """Dict with exporter=in_memory creates InMemoryExporter."""
        mock_inmem_cls.return_value = MagicMock()
        mock_tracing_cls.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        mock_inmem_cls.assert_called_once()

    @override_settings(APCORE_TRACING={"exporter": "tests.test_executor.FakeExporter"})
    @patch("apcore.observability.tracing.TracingMiddleware")
    @patch("apcore.Executor")
    def test_custom_dotted_path_exporter(self, mock_executor_cls, mock_tracing_cls):
        """Custom dotted path exporter is imported and instantiated."""
        mock_tracing_cls.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        # TracingMiddleware should be called with a FakeExporter instance
        call_kwargs = mock_tracing_cls.call_args.kwargs
        assert isinstance(call_kwargs["exporter"], FakeExporter)

    @patch("apcore.Executor")
    def test_no_tracing_middleware_by_default(self, mock_executor_cls):
        """No tracing middleware when APCORE_TRACING is not set."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        call_kwargs = mock_executor_cls.call_args
        middlewares = call_kwargs.kwargs.get("middlewares", [])
        assert middlewares == []


class TestTracingExporterShutdown:
    """Test OTLP exporter shutdown on reset."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(
        APCORE_TRACING={
            "exporter": "otlp",
            "otlp_endpoint": "http://localhost:4318",
        }
    )
    @patch("apcore.observability.tracing.OTLPExporter")
    @patch("apcore.observability.tracing.TracingMiddleware")
    @patch("apcore.Executor")
    def test_otlp_exporter_shutdown_on_reset(
        self, mock_executor_cls, mock_tracing_cls, mock_otlp_cls
    ):
        """OTLPExporter.shutdown() is called on _reset_executor()."""
        mock_exporter = MagicMock()
        mock_otlp_cls.return_value = mock_exporter
        mock_tracing_cls.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import _reset_executor, get_executor

        get_executor()
        _reset_executor()
        mock_exporter.shutdown.assert_called_once()

    @override_settings(APCORE_TRACING=True)
    @patch("apcore.observability.tracing.StdoutExporter")
    @patch("apcore.observability.tracing.TracingMiddleware")
    @patch("apcore.Executor")
    def test_exporter_without_shutdown_does_not_error(
        self, mock_executor_cls, mock_tracing_cls, mock_exporter_cls
    ):
        """Exporters without shutdown() method don't cause errors."""
        mock_exporter = MagicMock(spec=[])  # No methods
        mock_exporter_cls.return_value = mock_exporter
        mock_tracing_cls.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import _reset_executor, get_executor

        get_executor()
        # Should not raise
        _reset_executor()


class TestMetricsMiddlewareIntegration:
    """Test MetricsMiddleware integration in get_executor()."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(APCORE_METRICS=True)
    @patch("apcore.observability.metrics.MetricsCollector")
    @patch("apcore.observability.metrics.MetricsMiddleware")
    @patch("apcore.Executor")
    def test_metrics_true_prepends_metrics_middleware(
        self, mock_executor_cls, mock_mw_cls, mock_collector_cls
    ):
        """APCORE_METRICS=True prepends MetricsMiddleware."""
        mock_mw_instance = MagicMock()
        mock_mw_cls.return_value = mock_mw_instance
        mock_collector_cls.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        call_kwargs = mock_executor_cls.call_args
        middlewares = call_kwargs.kwargs.get("middlewares", [])
        assert mock_mw_instance in middlewares

    @override_settings(APCORE_METRICS={"buckets": [0.01, 0.05, 0.1]})
    @patch("apcore.observability.metrics.MetricsCollector")
    @patch("apcore.observability.metrics.MetricsMiddleware")
    @patch("apcore.Executor")
    def test_custom_buckets_passed_to_collector(
        self, mock_executor_cls, mock_mw_cls, mock_collector_cls
    ):
        """Custom buckets dict is passed to MetricsCollector."""
        mock_collector_cls.return_value = MagicMock()
        mock_mw_cls.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        mock_collector_cls.assert_called_once_with(buckets=[0.01, 0.05, 0.1])

    @patch("apcore.Executor")
    def test_no_metrics_middleware_by_default(self, mock_executor_cls):
        """No metrics middleware when APCORE_METRICS is not set."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        call_kwargs = mock_executor_cls.call_args
        middlewares = call_kwargs.kwargs.get("middlewares", [])
        assert middlewares == []

    def test_get_metrics_collector_returns_none_when_disabled(self):
        """get_metrics_collector() returns None when metrics disabled."""
        from django_apcore.registry import get_metrics_collector

        result = get_metrics_collector()
        assert result is None

    @override_settings(APCORE_METRICS=True)
    @patch("apcore.observability.metrics.MetricsCollector")
    def test_get_metrics_collector_singleton(self, mock_collector_cls):
        """get_metrics_collector() returns singleton MetricsCollector."""
        mock_instance = MagicMock()
        mock_collector_cls.return_value = mock_instance

        from django_apcore.registry import get_metrics_collector

        c1 = get_metrics_collector()
        c2 = get_metrics_collector()
        assert c1 is c2
        assert c1 is mock_instance
        mock_collector_cls.assert_called_once()

    @override_settings(APCORE_METRICS=True)
    @patch("apcore.observability.metrics.MetricsCollector")
    def test_reset_clears_metrics_collector(self, mock_collector_cls):
        """_reset_metrics_collector() clears the singleton."""
        mock_collector_cls.return_value = MagicMock()

        from django_apcore.registry import (
            _reset_metrics_collector,
            get_metrics_collector,
        )

        c1 = get_metrics_collector()
        _reset_metrics_collector()
        mock_collector_cls.return_value = MagicMock()
        c2 = get_metrics_collector()
        assert c1 is not c2

    def test_reset_registry_clears_metrics_collector(self):
        """_reset_registry() also resets metrics collector."""
        import django_apcore.registry as reg
        from django_apcore.registry import _reset_registry

        reg._metrics_collector = MagicMock()
        _reset_registry()
        assert reg._metrics_collector is None

    @override_settings(APCORE_METRICS=True)
    @patch("apcore.observability.metrics.MetricsCollector")
    def test_get_metrics_collector_returns_collector_when_enabled(
        self, mock_collector_cls
    ):
        """get_metrics_collector() returns MetricsCollector when enabled."""
        mock_instance = MagicMock()
        mock_collector_cls.return_value = mock_instance

        from django_apcore.registry import get_metrics_collector

        result = get_metrics_collector()
        assert result is mock_instance

    @override_settings(APCORE_METRICS=True)
    @patch("apcore.observability.metrics.MetricsMiddleware")
    @patch("apcore.observability.metrics.MetricsCollector")
    @patch("apcore.Executor")
    def test_metrics_collector_shared_with_middleware(
        self, mock_executor_cls, mock_collector_cls, mock_mw_cls
    ):
        """MetricsMiddleware receives the same collector singleton."""
        mock_collector = MagicMock()
        mock_collector_cls.return_value = mock_collector
        mock_mw_cls.return_value = MagicMock()
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        mock_mw_cls.assert_called_once_with(collector=mock_collector)


class TestGetContextFactory:
    """Test the get_context_factory() singleton."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def test_returns_django_context_factory_by_default(self):
        """Default factory is DjangoContextFactory."""
        from django_apcore.context import DjangoContextFactory
        from django_apcore.registry import get_context_factory

        factory = get_context_factory()
        assert isinstance(factory, DjangoContextFactory)

    def test_singleton_returns_same_instance(self):
        """get_context_factory() returns the same instance."""
        from django_apcore.registry import get_context_factory

        f1 = get_context_factory()
        f2 = get_context_factory()
        assert f1 is f2

    @override_settings(
        APCORE_CONTEXT_FACTORY=("tests.test_executor.FakeContextFactory")
    )
    def test_custom_factory_from_settings(self):
        """APCORE_CONTEXT_FACTORY resolves custom class."""
        from django_apcore.registry import get_context_factory

        factory = get_context_factory()
        assert isinstance(factory, FakeContextFactory)

    def test_reset_registry_also_resets_context_factory(self):
        """_reset_registry() clears context factory."""
        import django_apcore.registry as reg
        from django_apcore.registry import _reset_registry

        reg._context_factory = MagicMock()
        _reset_registry()
        assert reg._context_factory is None

    def test_factory_has_create_context(self):
        """Factory satisfies the ContextFactory protocol."""
        from django_apcore.registry import get_context_factory

        factory = get_context_factory()
        assert hasattr(factory, "create_context")
        assert callable(factory.create_context)


class FakeMiddleware:
    """Fake middleware for testing."""

    pass


class FakeExporter:
    """Fake tracing exporter for testing dotted path resolution."""

    pass


class FakeContextFactory:
    """Fake context factory for testing."""

    def create_context(self, request):  # noqa: ARG002
        return MagicMock()

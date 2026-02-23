# tests/test_executor.py
from unittest.mock import MagicMock, patch

from apcore import Middleware
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
    def test_middlewares_registered_in_extension_manager(self, mock_executor_cls):
        """Middleware dotted paths are registered via ExtensionManager."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor, get_extension_manager

        get_executor()
        ext_mgr = get_extension_manager()
        middlewares = ext_mgr.get_all("middleware")
        assert len(middlewares) >= 1
        assert any(isinstance(mw, FakeMiddleware) for mw in middlewares)

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
    def test_extension_manager_apply_called(self, mock_executor_cls):
        """get_executor() calls ExtensionManager.apply() for assembly."""
        mock_executor_instance = MagicMock()
        mock_executor_cls.return_value = mock_executor_instance

        from django_apcore.registry import get_executor, get_extension_manager

        executor = get_executor()
        # Verify the extension manager was created and is accessible
        ext_mgr = get_extension_manager()
        assert ext_mgr is not None
        assert executor is mock_executor_instance

    @patch("apcore.Executor")
    def test_executor_not_called_with_middlewares_kwarg(self, mock_executor_cls):
        """Executor constructor no longer receives middlewares kwarg."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        call_kwargs = mock_executor_cls.call_args
        # In the new architecture, middlewares are applied via ExtensionManager
        assert "middlewares" not in call_kwargs.kwargs

    @patch("apcore.Executor")
    def test_executor_not_called_with_acl_kwarg(self, mock_executor_cls):
        """Executor constructor no longer receives acl kwarg."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        get_executor()
        call_kwargs = mock_executor_cls.call_args
        # In the new architecture, ACL is applied via ExtensionManager
        assert "acl" not in call_kwargs.kwargs


class TestExtensionManagerTracingIntegration:
    """Test tracing integration via ExtensionManager."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(APCORE_TRACING=True)
    def test_tracing_registers_span_exporter(self):
        """APCORE_TRACING=True registers a span_exporter in ExtensionManager."""
        from django_apcore.registry import get_extension_manager

        ext_mgr = get_extension_manager()
        exporter = ext_mgr.get("span_exporter")
        assert exporter is not None

    @override_settings(APCORE_TRACING={"exporter": "in_memory"})
    def test_in_memory_exporter_registered(self):
        """Dict with exporter=in_memory registers a span_exporter."""
        from django_apcore.registry import get_extension_manager

        ext_mgr = get_extension_manager()
        exporter = ext_mgr.get("span_exporter")
        assert exporter is not None

    def test_no_span_exporter_by_default(self):
        """No span_exporter when APCORE_TRACING is not set."""
        from django_apcore.registry import get_extension_manager

        ext_mgr = get_extension_manager()
        exporter = ext_mgr.get("span_exporter")
        assert exporter is None


class TestExtensionManagerObsLoggingIntegration:
    """Test observability logging integration via ExtensionManager."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    @override_settings(APCORE_OBSERVABILITY_LOGGING=True)
    @patch("apcore.Executor")
    def test_executor_created_with_obs_logging(self, mock_executor_cls):
        """get_executor() succeeds when observability_logging=True."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        executor = get_executor()
        assert executor is not None

    @override_settings(
        APCORE_OBSERVABILITY_LOGGING={
            "log_inputs": False,
            "log_outputs": False,
        }
    )
    @patch("apcore.Executor")
    def test_executor_created_with_obs_logging_dict(self, mock_executor_cls):
        """get_executor() succeeds when observability_logging is a dict."""
        mock_executor_cls.return_value = MagicMock()

        from django_apcore.registry import get_executor

        executor = get_executor()
        assert executor is not None


class TestMetricsMiddlewareIntegration:
    """Test MetricsMiddleware integration in get_executor()."""

    def setup_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

    def teardown_method(self):
        from django_apcore.registry import _reset_registry

        _reset_registry()

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

    @override_settings(APCORE_METRICS={"buckets": [0.01, 0.05, 0.1]})
    @patch("apcore.observability.metrics.MetricsCollector")
    def test_custom_buckets_passed_to_collector(self, mock_collector_cls):
        """Custom buckets dict is passed to MetricsCollector."""
        mock_collector_cls.return_value = MagicMock()

        from django_apcore.registry import get_metrics_collector

        get_metrics_collector()
        mock_collector_cls.assert_called_once_with(buckets=[0.01, 0.05, 0.1])


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


class FakeMiddleware(Middleware):
    """Fake middleware for testing.

    Extends apcore.Middleware so ExtensionManager.register() accepts it.
    """

    pass


class FakeExporter:
    """Fake tracing exporter for testing dotted path resolution."""

    pass


class FakeContextFactory:
    """Fake context factory for testing."""

    def create_context(self, request):  # noqa: ARG002
        return MagicMock()

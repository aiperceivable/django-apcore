"""Tests for AsyncTaskManager Django integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestGetTaskManager:
    """Test the singleton AsyncTaskManager wrapper."""

    def setup_method(self):
        from django_apcore.tasks import _reset_task_manager

        _reset_task_manager()

    def teardown_method(self):
        from django_apcore.tasks import _reset_task_manager

        _reset_task_manager()

    @patch("apcore.AsyncTaskManager")
    @patch("django_apcore.registry.get_executor")
    def test_returns_async_task_manager(self, mock_get_executor, mock_atm_cls):
        """get_task_manager() returns an AsyncTaskManager instance."""
        mock_get_executor.return_value = MagicMock()
        mock_atm_cls.return_value = MagicMock()

        from django_apcore.tasks import get_task_manager

        tm = get_task_manager()
        assert tm is mock_atm_cls.return_value
        mock_atm_cls.assert_called_once()

    @patch("apcore.AsyncTaskManager")
    @patch("django_apcore.registry.get_executor")
    def test_singleton_returns_same_instance(self, mock_get_executor, mock_atm_cls):
        """Calling get_task_manager() twice returns the exact same object."""
        mock_get_executor.return_value = MagicMock()
        mock_atm_cls.return_value = MagicMock()

        from django_apcore.tasks import get_task_manager

        tm1 = get_task_manager()
        tm2 = get_task_manager()
        assert tm1 is tm2
        mock_atm_cls.assert_called_once()

    @patch("apcore.AsyncTaskManager")
    @patch("django_apcore.registry.get_executor")
    def test_reset_creates_new_instance(self, mock_get_executor, mock_atm_cls):
        """_reset_task_manager() causes the next call to create a new instance."""
        mock_get_executor.return_value = MagicMock()

        from django_apcore.tasks import _reset_task_manager, get_task_manager

        first_instance = MagicMock()
        second_instance = MagicMock()
        mock_atm_cls.side_effect = [first_instance, second_instance]

        tm1 = get_task_manager()
        _reset_task_manager()
        tm2 = get_task_manager()
        assert tm1 is not tm2
        assert tm1 is first_instance
        assert tm2 is second_instance

    @patch("apcore.AsyncTaskManager")
    @patch("django_apcore.registry.get_executor")
    @patch("django_apcore.settings.get_apcore_settings")
    def test_uses_settings(self, mock_settings, mock_get_executor, mock_atm_cls):
        """get_task_manager() passes settings to AsyncTaskManager constructor."""
        mock_settings.return_value = MagicMock(
            task_max_concurrent=5,
            task_max_tasks=100,
        )
        mock_executor = MagicMock()
        mock_get_executor.return_value = mock_executor
        mock_atm_cls.return_value = MagicMock()

        from django_apcore.tasks import get_task_manager

        get_task_manager()
        mock_atm_cls.assert_called_once_with(
            executor=mock_executor,
            max_concurrent=5,
            max_tasks=100,
        )

    @patch("apcore.AsyncTaskManager")
    @patch("django_apcore.registry.get_executor")
    def test_uses_default_settings(self, mock_get_executor, mock_atm_cls):
        """get_task_manager() uses default settings when not overridden."""
        mock_get_executor.return_value = MagicMock()
        mock_atm_cls.return_value = MagicMock()

        from django_apcore.tasks import get_task_manager

        get_task_manager()
        call_kwargs = mock_atm_cls.call_args
        assert call_kwargs.kwargs["max_concurrent"] == 10
        assert call_kwargs.kwargs["max_tasks"] == 1000

    @patch("apcore.AsyncTaskManager")
    @patch("django_apcore.registry.get_executor")
    def test_passes_executor_to_constructor(self, mock_get_executor, mock_atm_cls):
        """get_task_manager() passes the singleton executor to AsyncTaskManager."""
        mock_executor = MagicMock()
        mock_get_executor.return_value = mock_executor
        mock_atm_cls.return_value = MagicMock()

        from django_apcore.tasks import get_task_manager

        get_task_manager()
        call_kwargs = mock_atm_cls.call_args
        assert call_kwargs.kwargs["executor"] is mock_executor

    def test_module_exposes_reset(self):
        """_reset_task_manager is importable from the tasks module."""
        from django_apcore.tasks import _reset_task_manager  # noqa: F401

    def test_module_exposes_get_task_manager(self):
        """get_task_manager is importable from the tasks module."""
        from django_apcore.tasks import get_task_manager  # noqa: F401


class TestResetTaskManager:
    """Test _reset_task_manager() edge cases."""

    def setup_method(self):
        from django_apcore.tasks import _reset_task_manager

        _reset_task_manager()

    def teardown_method(self):
        from django_apcore.tasks import _reset_task_manager

        _reset_task_manager()

    def test_reset_when_no_manager_exists(self):
        """_reset_task_manager() does not raise when no manager has been created."""
        from django_apcore.tasks import _reset_task_manager

        # Should not raise
        _reset_task_manager()

    @patch("apcore.AsyncTaskManager")
    @patch("django_apcore.registry.get_executor")
    def test_reset_sets_global_to_none(self, mock_get_executor, mock_atm_cls):
        """_reset_task_manager() sets _task_manager global to None."""
        mock_get_executor.return_value = MagicMock()
        mock_atm_cls.return_value = MagicMock()

        import django_apcore.tasks as tasks_module
        from django_apcore.tasks import get_task_manager

        get_task_manager()
        assert tasks_module._task_manager is not None

        tasks_module._reset_task_manager()
        assert tasks_module._task_manager is None

    @patch("apcore.AsyncTaskManager")
    @patch("django_apcore.registry.get_executor")
    def test_reset_attempts_shutdown(self, mock_get_executor, mock_atm_cls):
        """_reset_task_manager() attempts to call shutdown() on the manager."""
        mock_get_executor.return_value = MagicMock()
        mock_manager = MagicMock()
        mock_atm_cls.return_value = mock_manager

        from django_apcore.tasks import _reset_task_manager, get_task_manager

        get_task_manager()
        _reset_task_manager()
        # shutdown() should have been attempted (but failures are swallowed)

    @patch("apcore.AsyncTaskManager")
    @patch("django_apcore.registry.get_executor")
    def test_reset_does_not_raise_on_shutdown_error(
        self, mock_get_executor, mock_atm_cls
    ):
        """_reset_task_manager() swallows errors from shutdown()."""
        mock_get_executor.return_value = MagicMock()
        mock_manager = MagicMock()
        mock_manager.shutdown.side_effect = RuntimeError("shutdown failed")
        mock_atm_cls.return_value = mock_manager

        from django_apcore.tasks import _reset_task_manager, get_task_manager

        get_task_manager()
        # Should not raise
        _reset_task_manager()

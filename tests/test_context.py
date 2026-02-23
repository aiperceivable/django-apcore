# tests/test_context.py
from unittest.mock import MagicMock, patch


class TestDjangoContextFactory:
    """Test the DjangoContextFactory."""

    @patch("apcore.Context")
    @patch("apcore.Identity")
    def test_authenticated_user(self, mock_identity_cls, mock_context_cls):
        """Authenticated user produces user Identity."""
        from django_apcore.context import DjangoContextFactory

        user = MagicMock()
        user.is_authenticated = True
        user.pk = 42
        user.is_staff = False
        user.is_superuser = False
        user.groups.values_list.return_value = ["editors", "viewers"]

        request = MagicMock()
        request.user = user

        mock_identity = MagicMock()
        mock_identity_cls.return_value = mock_identity

        factory = DjangoContextFactory()
        factory.create_context(request)

        mock_identity_cls.assert_called_once_with(
            id="42",
            type="user",
            roles=["editors", "viewers"],
            attrs={"is_staff": False, "is_superuser": False},
        )
        mock_context_cls.create.assert_called_once_with(
            identity=mock_identity,
        )

    @patch("apcore.Context")
    @patch("apcore.Identity")
    def test_anonymous_user(self, mock_identity_cls, mock_context_cls):
        """Anonymous user produces anonymous Identity."""
        from django_apcore.context import DjangoContextFactory

        user = MagicMock()
        user.is_authenticated = False

        request = MagicMock()
        request.user = user

        factory = DjangoContextFactory()
        factory.create_context(request)

        mock_identity_cls.assert_called_once_with(
            id="anonymous",
            type="anonymous",
        )

    @patch("apcore.Context")
    @patch("apcore.Identity")
    def test_no_user_attribute(self, mock_identity_cls, mock_context_cls):
        """Request without .user produces anonymous Identity."""
        from django_apcore.context import DjangoContextFactory

        request = MagicMock(spec=[])  # no attributes

        factory = DjangoContextFactory()
        factory.create_context(request)

        mock_identity_cls.assert_called_once_with(
            id="anonymous",
            type="anonymous",
        )

    @patch("apcore.Context")
    @patch("apcore.Identity")
    def test_group_extraction(self, mock_identity_cls, mock_context_cls):
        """Groups are extracted from user.groups."""
        from django_apcore.context import DjangoContextFactory

        user = MagicMock()
        user.is_authenticated = True
        user.pk = 1
        user.is_staff = True
        user.is_superuser = True
        user.groups.values_list.return_value = ["admin", "staff"]

        request = MagicMock()
        request.user = user

        factory = DjangoContextFactory()
        factory.create_context(request)

        call_kwargs = mock_identity_cls.call_args.kwargs
        assert call_kwargs["roles"] == ["admin", "staff"]

    @patch("apcore.Context")
    @patch("apcore.Identity")
    def test_staff_superuser_attrs(self, mock_identity_cls, mock_context_cls):
        """is_staff and is_superuser are included in attrs."""
        from django_apcore.context import DjangoContextFactory

        user = MagicMock()
        user.is_authenticated = True
        user.pk = 1
        user.is_staff = True
        user.is_superuser = True
        user.groups.values_list.return_value = []

        request = MagicMock()
        request.user = user

        factory = DjangoContextFactory()
        factory.create_context(request)

        call_kwargs = mock_identity_cls.call_args.kwargs
        assert call_kwargs["attrs"]["is_staff"] is True
        assert call_kwargs["attrs"]["is_superuser"] is True

    @patch("apcore.Context")
    @patch("apcore.Identity")
    def test_group_failure_handling(self, mock_identity_cls, mock_context_cls):
        """If groups extraction fails, empty list is used."""
        from django_apcore.context import DjangoContextFactory

        user = MagicMock()
        user.is_authenticated = True
        user.pk = 1
        user.is_staff = False
        user.is_superuser = False
        user.groups.values_list.side_effect = Exception("DB error")

        request = MagicMock()
        request.user = user

        factory = DjangoContextFactory()
        factory.create_context(request)

        call_kwargs = mock_identity_cls.call_args.kwargs
        assert call_kwargs["roles"] == []

    def test_protocol_compliance(self):
        """DjangoContextFactory has the create_context method."""
        from django_apcore.context import DjangoContextFactory

        factory = DjangoContextFactory()
        assert hasattr(factory, "create_context")
        assert callable(factory.create_context)

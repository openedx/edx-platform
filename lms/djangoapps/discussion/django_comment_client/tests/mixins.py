"""
Mixin for django_comment_client tests.
"""

from unittest import mock


class MockForumApiMixin:
    """Mixin to mock forum_api across different test cases with a single mock instance."""

    @classmethod
    def setUpClass(cls):
        """Apply a single forum_api mock at the class level."""
        cls.setUpClassAndForumMock()

    @classmethod
    def setUpClassAndForumMock(cls):
        """
        Set up the class and apply the forum_api mock.
        """
        cls.mock_forum_api = mock.Mock()

        # TODO: Remove this after moving all APIs
        cls.flag_v2_patcher = mock.patch(
            "openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled"
        )
        cls.mock_enable_forum_v2 = cls.flag_v2_patcher.start()
        cls.mock_enable_forum_v2.return_value = True

        patch_targets = [
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api",
            "openedx.core.djangoapps.django_comment_common.comment_client.comment.forum_api",
            "openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api",
            "openedx.core.djangoapps.django_comment_common.comment_client.course.forum_api",
            "openedx.core.djangoapps.django_comment_common.comment_client.subscriptions.forum_api",
            "openedx.core.djangoapps.django_comment_common.comment_client.user.forum_api",
        ]
        cls.forum_api_patchers = [
            mock.patch(target, cls.mock_forum_api) for target in patch_targets
        ]
        for patcher in cls.forum_api_patchers:
            patcher.start()

    @classmethod
    def disposeForumMocks(cls):
        """Stop patches after tests complete."""
        cls.flag_v2_patcher.stop()

        for patcher in cls.forum_api_patchers:
            patcher.stop()

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        cls.disposeForumMocks()

    def set_mock_return_value(self, function_name, return_value):
        """
        Set a return value for a specific method in forum_api mock.

        Args:
            function_name (str): The method name in the mock to set a return value for.
            return_value (Any): The return value for the method.
        """
        setattr(
            self.mock_forum_api, function_name, mock.Mock(return_value=return_value)
        )

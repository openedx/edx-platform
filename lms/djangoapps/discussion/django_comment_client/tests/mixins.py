"""
Mixin for django_comment_client tests.
"""

from unittest import mock


class MockForumApiMixin:
    """Mixin to mock forum_api across different test cases with a single mock instance."""

    users_map = {}

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

    def set_mock_side_effect(self, function_name, side_effect_fn):
        """
        Set a side effect for a specific method in forum_api mock.

        Args:
            function_name (str): The method name in the mock to set a side effect for.
            side_effect_fn (Callable): A function to be called when the mock is called.
        """
        setattr(
            self.mock_forum_api, function_name, mock.Mock(side_effect=side_effect_fn)
        )

    def check_mock_called_with(self, function_name, index, *parms, **kwargs):
        """
        Check if a specific method in forum_api mock was called with the given parameters.

        Args:
            function_name (str): The method name in the mock to check.
            parms (tuple): The parameters to check the method was called with.
        """
        call_args = getattr(self.mock_forum_api, function_name).call_args_list[index]
        assert call_args == mock.call(*parms, **kwargs)

    def check_mock_called(self, function_name):
        """
        Check if a specific method in the forum_api mock was called.

        Args:
            function_name (str): The method name in the mock to check.

        Returns:
            bool: True if the method was called, False otherwise.
        """
        return getattr(self.mock_forum_api, function_name).called

    def get_mock_func_calls(self, function_name):
        """
        Returns a list of call arguments for a specific method in the mock_forum_api.

        Args:
            function_name (str): The name of the method in the mock_forum_api to retrieve call arguments for.

        Returns:
            list: A list of call arguments for the specified method.
        """
        return getattr(self.mock_forum_api, function_name).call_args_list

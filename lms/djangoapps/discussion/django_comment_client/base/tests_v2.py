import pytest

# pylint: skip-file
"""Tests for django forum V2."""


import logging
from unittest import mock
from unittest.mock import patch

import ddt
from django.core.management import call_command
from django.test.client import RequestFactory
from opaque_keys.edx.locator import CourseLocator
from common.djangoapps.util.testing import UrlResetMixin
from common.test.utils import MockSignalHandlerMixin, disable_signal
from lms.djangoapps.discussion.django_comment_client.base import views
from lms.djangoapps.discussion.django_comment_client.tests.group_id import (
    GroupIdAssertionMixin,
)
from lms.djangoapps.discussion.django_comment_client.tests.utils import (
    CohortedTestCase,
    ForumsEnableMixin,
)
from xmodule.modulestore.tests.django_utils import (
    SharedModuleStoreTestCase,
)
from xmodule.modulestore.tests.factories import CourseFactory

log = logging.getLogger(__name__)

CS_PREFIX = "http://localhost:4567/api/v1"


@patch(
    "openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled",
    autospec=True,
)
@disable_signal(views, "thread_edited")
@disable_signal(views, "thread_voted")
@disable_signal(views, "thread_deleted")
class ThreadActionGroupIdTestCase(CohortedTestCase, GroupIdAssertionMixin):

    def _get_mocked_instance_from_view_name(self, view_name):
        """
        Get the relavent Mock function based on the view_name
        """
        mocks = {
            "create_thread": self.mock_create_thread,
            "get_thread": self.mock_get_thread,
            "update_thread": self.mock_update_thread,
        }
        return mocks.get(view_name)

    def setUp(self):
        super().setUp()
        self.mock_create_thread = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api.create_thread",
            autospec=True,
        ).start()
        self.mock_get_thread = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_thread",
            autospec=True,
        ).start()
        self.mock_update_thread = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api.update_thread",
            autospec=True,
        ).start()
        self.mock_update_thread_flag = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.update_thread_flag",
            autospec=True,
        ).start()
        default_response = {
            "user_id": str(self.student.id),
            "group_id": self.student_cohort.id,
            "closed": False,
            "type": "thread",
            "commentable_id": "non_team_dummy_id",
            "body": "test body",
        }
        self.mock_create_thread.return_value = default_response
        self.mock_get_thread.return_value = default_response
        self.mock_update_thread.return_value = default_response
        self.mock_update_thread_flag.return_value = default_response

        self.mock_get_course_id_by_thread = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread",
            autospec=True,
        ).start()
        self.mock_get_course_id_by_thread.return_value = CourseLocator(
            "dummy", "test_123", "test_run"
        )

        self.addCleanup(mock.patch.stopall)  # Ensure all mocks are stopped after tests

    def call_view(
        self,
        view_name,
        mock_is_forum_v2_enabled,
        user=None,
        post_params=None,
        view_args=None,
    ):
        mocked_view = self._get_mocked_instance_from_view_name(view_name)
        mock_is_forum_v2_enabled.return_value = True
        if mocked_view:
            mocked_view.return_value = {
                "user_id": str(self.student.id),
                "group_id": self.student_cohort.id,
                "closed": False,
                "type": "thread",
                "commentable_id": "non_team_dummy_id",
                "body": "test body",
            }
        request = RequestFactory().post("dummy_url", post_params or {})
        request.user = user or self.student
        request.view_name = view_name

        return getattr(views, view_name)(
            request,
            course_id=str(self.course.id),
            thread_id="dummy",
            **(view_args or {}),
        )

    def test_flag(self, mock_is_forum_v2_enabled):
        with mock.patch(
            "openedx.core.djangoapps.django_comment_common.signals.thread_flagged.send"
        ) as signal_mock:
            response = self.call_view("flag_abuse_for_thread", mock_is_forum_v2_enabled)
            self._assert_json_response_contains_group_info(response)
            self.assertEqual(signal_mock.call_count, 1)
        response = self.call_view("un_flag_abuse_for_thread", mock_is_forum_v2_enabled)
        self._assert_json_response_contains_group_info(response)


@ddt.ddt
@disable_signal(views, "comment_flagged")
@disable_signal(views, "thread_flagged")
@patch(
    "openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled",
    autospec=True,
)
class ViewsTestCase(
    CohortedTestCase,
    ForumsEnableMixin,
    UrlResetMixin,
    SharedModuleStoreTestCase,
    MockSignalHandlerMixin,
):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create(
                org="MITx",
                course="999",
                discussion_topics={"Some Topic": {"id": "some_topic"}},
                display_name="Robot Super Course",
            )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.course_id = cls.course.id

        # seed the forums permissions and roles
        call_command("seed_permissions_roles", str(cls.course_id))

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        # Patching the ENABLE_DISCUSSION_SERVICE value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super().setUp()
        self.mock_get_course_id_by_comment = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api.get_course_id_by_comment"
        ).start()
        self.mock_get_course_id_by_comment.return_value = self.course.id
        self.mock_get_course_id_by_thread = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        ).start()
        self.mock_get_course_id_by_thread.return_value = self.course.id
        self.mock_create_thread = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api.create_thread",
            autospec=True,
        ).start()
        self.mock_get_thread = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_thread",
            autospec=True,
        ).start()
        self.mock_update_thread = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api.update_thread",
            autospec=True,
        ).start()
        self.mock_update_thread_flag = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.update_thread_flag",
            autospec=True,
        ).start()
        self.mock_update_comment_flag = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.update_comment_flag",
            autospec=True,
        ).start()
        default_response = {
            "user_id": str(self.student.id),
            "group_id": self.student_cohort.id,
            "closed": False,
            "type": "thread",
            "commentable_id": "non_team_dummy_id",
            "body": "test body",
        }
        self.mock_create_thread.return_value = default_response
        self.mock_get_thread.return_value = default_response
        self.mock_update_thread.return_value = default_response
        self.mock_update_thread_flag.return_value = default_response
        self.mock_update_comment_flag.return_value = default_response
        self.addCleanup(mock.patch.stopall)

    def test_flag_thread(self, mock_is_forum_v2_enabled):
        mock_is_forum_v2_enabled.return_value = True
        self.client.put(
            f"{CS_PREFIX}/threads/518d4237b023791dca00000d/abuse_flag",
            kwargs={
                "thread_id": "518d4237b023791dca00000d",
                "course_id": str(self.course_id),
            },
        )

    def test_un_flag_thread(self, mock_is_forum_v2_enabled):
        mock_is_forum_v2_enabled.return_value = True
        self.client.put(
            f"{CS_PREFIX}/threads/518d4237b023791dca00000d/abuse_unflag",
            kwargs={
                "thread_id": "518d4237b023791dca00000d",
                "course_id": str(self.course_id),
            },
        )

    def test_flag_comment(self, mock_is_forum_v2_enabled):
        mock_is_forum_v2_enabled.return_value = True
        self.client.put(
            f"{CS_PREFIX}/comments/518d4237b023791dca00000d/abuse_flag",
            kwargs={
                "comment_id": "518d4237b023791dca00000d",
                "course_id": str(self.course_id),
            },
        )

    def test_un_flag_comment(self, mock_is_forum_v2_enabled):
        mock_is_forum_v2_enabled.return_value = True
        self.client.put(
            f"{CS_PREFIX}/comments/518d4237b023791dca00000d/abuse_unflag",
            kwargs={
                "comment_id": "518d4237b023791dca00000d",
                "course_id": str(self.course_id),
            },
        )

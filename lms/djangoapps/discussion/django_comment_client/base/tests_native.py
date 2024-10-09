import pytest
# pylint: skip-file
"""Tests for django comment client views."""


import json
import logging
from contextlib import contextmanager
from unittest import mock
from unittest.mock import ANY, Mock, patch

import ddt
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test.client import RequestFactory
from django.urls import reverse
from eventtracking.processors.exceptions import EventEmissionExit
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator
from openedx_events.learning.signals import FORUM_THREAD_CREATED, FORUM_THREAD_RESPONSE_CREATED, FORUM_RESPONSE_COMMENT_CREATED

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.roles import CourseStaffRole, UserBasedRole
from common.djangoapps.student.tests.factories import CourseAccessRoleFactory, CourseEnrollmentFactory, UserFactory
from common.djangoapps.track.middleware import TrackMiddleware
from common.djangoapps.track.views import segmentio
from common.djangoapps.track.views.tests.base import SEGMENTIO_TEST_USER_ID, SegmentIOTrackingTestCaseBase
from common.djangoapps.util.testing import UrlResetMixin
from common.test.utils import MockSignalHandlerMixin, disable_signal
from lms.djangoapps.discussion.django_comment_client.base import views
from lms.djangoapps.discussion.django_comment_client.tests.group_id_v2 import (
    CohortedTopicGroupIdTestMixin,
    GroupIdAssertionMixin,
    NonCohortedTopicGroupIdTestMixin
)
from lms.djangoapps.discussion.django_comment_client.tests.unicode import UnicodeTestMixin
from lms.djangoapps.discussion.django_comment_client.tests.utils import CohortedTestCase, ForumsEnableMixin
from lms.djangoapps.teams.tests.factories import CourseTeamFactory, CourseTeamMembershipFactory
from openedx.core.djangoapps.course_groups.cohorts import set_course_cohorted
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from openedx.core.djangoapps.django_comment_common.comment_client import Thread
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_STUDENT,
    CourseDiscussionSettings,
    Role,
    assign_role
)
from openedx.core.djangoapps.django_comment_common.utils import (
    ThreadContext,
    seed_permissions_roles,
)
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
from openedx.core.lib.teams_config import TeamsConfig
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase, SharedModuleStoreTestCase,
)
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory, check_mongo_calls

from .event_transformers import ForumThreadViewedEventTransformer

log = logging.getLogger(__name__)

QUERY_COUNT_TABLE_IGNORELIST = WAFFLE_TABLES

# pylint: disable=missing-docstring


@patch('lms.djangoapps.discussion.toggles.ENABLE_FORUM_V2.is_enabled', return_value=True)
@patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.create_thread', autospec=True)
class CreateThreadGroupIdTestCase(
        CohortedTestCase,
        CohortedTopicGroupIdTestMixin,
        NonCohortedTopicGroupIdTestMixin
):
    cs_endpoint = "/threads"

    def call_view(self, mock_create_thread, mock_is_forum_v2_enabled, commentable_id, user, group_id, pass_group_id=True):
        mock_create_thread.return_value = {}
        request_data = {"body": "body", "title": "title", "thread_type": "discussion"}
        if pass_group_id:
            request_data["group_id"] = group_id
        request = RequestFactory().post("dummy_url", request_data)
        request.user = user
        request.view_name = "create_thread"

        return views.create_thread(
            request,
            course_id=str(self.course.id),
            commentable_id=commentable_id
        )

    def test_group_info_in_response(self, mock_is_forum_v2_enabled, mock_request):
        response = self.call_view(
            mock_is_forum_v2_enabled,
            mock_request,
            "cohorted_topic",
            self.student,
            ''
        )
        self._assert_json_response_contains_group_info(response)


def get_forum_api_mock(view_name, mock_forum_api):
    mocks = {
        "create_thread": mock_forum_api.create_thread,
        "update_thread": mock_forum_api.update_thread,
        "delete_thread": mock_forum_api.delete_thread,
        "get_thread": mock_forum_api.get_thread,
    }
    return mocks.get(view_name, None)


@patch('lms.djangoapps.discussion.toggles.ENABLE_FORUM_V2.is_enabled', return_value=True)
@disable_signal(views, 'thread_edited')
@disable_signal(views, 'thread_voted')
@disable_signal(views, 'thread_deleted')
class ThreadActionGroupIdTestCase(
        CohortedTestCase,
        GroupIdAssertionMixin
):
    
    def _get_mocked_instance_from_view_name(self, view_name):
        """
        Get the relavent Mock function based on the view_name
        """
        mocks = {
            "create_thread": self.mock_create_thread,
            "get_thread": self.mock_get_thread,
            "update_thread": self.mock_update_thread,
            "delete_thread": self.mock_delete_thread,
            "vote_for_thread": self.mock_update_thread_votes,
        }
        return mocks.get(view_name)
    
    def setUp(self):
        super().setUp()
        # Mocking create_thread and get_thread methods
        self.mock_create_thread = mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.create_thread', autospec=True).start()
        self.mock_get_thread = mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_thread', autospec=True).start()
        self.mock_update_thread = mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api.update_thread', autospec=True).start()
        self.mock_delete_thread = mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api.delete_thread', autospec=True).start()
        self.mock_update_thread_votes = mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.user.forum_api.update_thread_votes', autospec=True).start()
        self.mock_delete_thread_vote = mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.user.forum_api.delete_thread_vote', autospec=True).start()
        self.mock_update_thread_flag = mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.update_thread_flag', autospec=True).start()
        self.mock_pin_thread = mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.pin_thread', autospec=True).start()
        self.mock_unpin_thread = mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.unpin_thread', autospec=True).start()



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
        self.mock_delete_thread.return_value = default_response
        self.mock_update_thread_votes.return_value = default_response
        self.mock_delete_thread_vote = default_response
        self.mock_update_thread_flag = default_response
        self.mock_pin_thread = default_response
        self.mock_unpin_thread = default_response
        
        self.get_course_id_by_thread = mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread', autospec=True).start()
        self.get_course_id_by_thread.return_value = CourseLocator('dummy', 'test_123', 'test_run')
        
        self.addCleanup(mock.patch.stopall)  # Ensure all mocks are stopped after tests
    

    def call_view(
            self,
            view_name,
            mock_is_forum_v2_enabled,
            user=None,
            post_params=None,
            view_args=None
    ):
        mocked_view = self._get_mocked_instance_from_view_name(view_name)
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
            **(view_args or {})
        )

    def test_update(self, mock_is_forum_v2_enabled):
        response = self.call_view(
            "update_thread",
            mock_is_forum_v2_enabled,
            post_params={"body": "body", "title": "title"}
        )
        self._assert_json_response_contains_group_info(response)

    def test_delete(self, mock_is_forum_v2_enabled):
        response = self.call_view("delete_thread", mock_is_forum_v2_enabled)
        self._assert_json_response_contains_group_info(response)

    def test_vote(self, mock_is_forum_v2_enabled):
        response = self.call_view(
            "vote_for_thread",
            mock_is_forum_v2_enabled,
            view_args={"value": "up"}
        )
        self._assert_json_response_contains_group_info(response)
        response = self.call_view("undo_vote_for_thread", mock_is_forum_v2_enabled)
        self._assert_json_response_contains_group_info(response)

    def test_flag(self, mock_is_forum_v2_enabled):
        with mock.patch('openedx.core.djangoapps.django_comment_common.signals.thread_flagged.send') as signal_mock:
            response = self.call_view("flag_abuse_for_thread", mock_is_forum_v2_enabled)
            self._assert_json_response_contains_group_info(response)
            self.assertEqual(signal_mock.call_count, 1)
        response = self.call_view("un_flag_abuse_for_thread", mock_is_forum_v2_enabled)
        self._assert_json_response_contains_group_info(response)

    def test_pin(self, mock_is_forum_v2_enabled):
        response = self.call_view(
            "pin_thread",
            mock_is_forum_v2_enabled,
            user=self.moderator
        )
        self._assert_json_response_contains_group_info(response)
        response = self.call_view(
            "un_pin_thread",
            mock_is_forum_v2_enabled,
            user=self.moderator
        )
        self._assert_json_response_contains_group_info(response)

    def test_openclose(self, mock_is_forum_v2_enabled):
        response = self.call_view(
            "openclose_thread",
            mock_is_forum_v2_enabled,
            user=self.moderator
        )
        self._assert_json_response_contains_group_info(
            response,
            lambda d: d['content']
        )



# @disable_signal(views, 'thread_edited')
# @disable_signal(views, 'thread_voted')
# @disable_signal(views, 'thread_deleted')
# class ThreadActionGroupIdTestCase(
#         CohortedTestCase,
#         GroupIdAssertionMixin
# ):
#     def call_view(
#             self,
#             view_name,
#             mock_request,
#             user=None,
#             post_params=None,
#             view_args=None
#     ):
#         self._set_mock_request_data(
#             mock_request,
#             {
#                 "user_id": str(self.student.id),
#                 "group_id": self.student_cohort.id,
#                 "closed": False,
#                 "type": "thread",
#                 "commentable_id": "non_team_dummy_id",
#                 "body": "test body",
#             }
#         )
#         request = RequestFactory().post("dummy_url", post_params or {})
#         request.user = user or self.student
#         request.view_name = view_name

#         return getattr(views, view_name)(
#             request,
#             course_id=str(self.course.id),
#             thread_id="dummy",
#             **(view_args or {})
#         )

#     @patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.pin_thread', autospec=True)
#     def test_pin(self, mock_pin_thread):
#         response = self.call_view(
#             "pin_thread",
#             mock_pin_thread,
#             user=self.moderator
#         )
#         self._assert_json_response_contains_group_info(response)
    
#     @patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.unpin_thread', autospec=True)
#     def test_unpin(self, mock_unpin_thread):
#         response = self.call_view(
#             "un_pin_thread",
#             mock_unpin_thread,
#             user=self.moderator
#         )
#         self._assert_json_response_contains_group_info(response)

 
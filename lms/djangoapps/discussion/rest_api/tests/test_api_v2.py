# pylint: skip-file
"""
Tests for Discussion API internal interface
"""

import itertools
import random
from datetime import datetime, timedelta
from unittest import mock
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import ddt
import httpretty
import pytest
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test.client import RequestFactory
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator
from pytz import UTC
from rest_framework.exceptions import PermissionDenied

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    SharedModuleStoreTestCase,
)
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory
from xmodule.partitions.partitions import Group, UserPartition

from common.djangoapps.student.tests.factories import (
    AdminFactory,
    BetaTesterFactory,
    CourseEnrollmentFactory,
    StaffFactory,
    UserFactory,
)
from common.djangoapps.util.testing import UrlResetMixin
from common.test.utils import MockSignalHandlerMixin, disable_signal
from lms.djangoapps.discussion.django_comment_client.tests.utils import (
    ForumsEnableMixin,
)
from lms.djangoapps.discussion.tests.utils import (
    make_minimal_cs_comment,
    make_minimal_cs_thread,
)
from lms.djangoapps.discussion.rest_api import api
from lms.djangoapps.discussion.rest_api.api import (
    create_comment,
    create_thread,
    delete_comment,
    delete_thread,
    get_comment_list,
    get_course,
    get_course_topics,
    get_course_topics_v2,
    get_thread,
    get_thread_list,
    get_user_comments,
    update_comment,
    update_thread,
)
from lms.djangoapps.discussion.rest_api.exceptions import (
    CommentNotFoundError,
    DiscussionBlackOutException,
    DiscussionDisabledError,
    ThreadNotFoundError,
)
from lms.djangoapps.discussion.rest_api.serializers import TopicOrdering
from lms.djangoapps.discussion.rest_api.tests.utils import (
    CommentsServiceMockMixin,
    ForumMockUtilsMixin,
    make_paginated_api_response,
    parsed_body,
)
from openedx.core.djangoapps.course_groups.models import CourseUserGroupPartitionGroup
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from openedx.core.djangoapps.discussions.models import (
    DiscussionsConfiguration,
    DiscussionTopicLink,
    Provider,
    PostingRestriction,
)
from openedx.core.djangoapps.discussions.tasks import (
    update_discussions_settings_from_course_task,
)
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_MODERATOR,
    FORUM_ROLE_STUDENT,
    Role,
)
from openedx.core.lib.exceptions import CourseNotFoundError, PageNotFoundError

User = get_user_model()


def _remove_discussion_tab(course, user_id):
    """
    Remove the discussion tab for the course.

    user_id is passed to the modulestore as the editor of the xblock.
    """
    course.tabs = [tab for tab in course.tabs if not tab.type == "discussion"]
    modulestore().update_item(course, user_id)


def _discussion_disabled_course_for(user):
    """
    Create and return a course with discussions disabled.

    The user passed in will be enrolled in the course.
    """
    course_with_disabled_forums = CourseFactory.create()
    CourseEnrollmentFactory.create(user=user, course_id=course_with_disabled_forums.id)
    _remove_discussion_tab(course_with_disabled_forums, user.id)

    return course_with_disabled_forums


def _assign_role_to_user(user, course_id, role):
    """
    Unset the blackout period for course discussions.

    Arguments:
            user: User to assign role to
            course_id: Course id of the course user will be assigned role in
            role: Role assigned to user for course
    """
    role = Role.objects.create(name=role, course_id=course_id)
    role.users.set([user])


def _create_course_and_cohort_with_user_role(course_is_cohorted, user, role_name):
    """
    Creates a course with the value of `course_is_cohorted`, plus `always_cohort_inline_discussions`
    set to True (which is no longer the default value). Then 1) enrolls the user in that course,
    2) creates a cohort that the user is placed in, and 3) adds the user to the given role.

    Returns: a tuple of the created course and the created cohort
    """
    cohort_course = CourseFactory.create(
        cohort_config={
            "cohorted": course_is_cohorted,
            "always_cohort_inline_discussions": True,
        }
    )
    CourseEnrollmentFactory.create(user=user, course_id=cohort_course.id)
    cohort = CohortFactory.create(course_id=cohort_course.id, users=[user])
    _assign_role_to_user(user=user, course_id=cohort_course.id, role=role_name)

    return [cohort_course, cohort]


def _set_course_discussion_blackout(course, user_id):
    """
    Set the blackout period for course discussions.

    Arguments:
            course: Course for which blackout period is set
            user_id: User id of user enrolled in the course
    """
    course.discussion_blackouts = [
        datetime.now(UTC) - timedelta(days=3),
        datetime.now(UTC) + timedelta(days=3),
    ]
    configuration = DiscussionsConfiguration.get(course.id)
    configuration.posting_restrictions = PostingRestriction.SCHEDULED
    configuration.save()
    modulestore().update_item(course, user_id)


@ddt.ddt
@disable_signal(api, "thread_created")
@disable_signal(api, "thread_voted")
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CreateThreadTest(
    ForumsEnableMixin,
    UrlResetMixin,
    SharedModuleStoreTestCase,
    MockSignalHandlerMixin,
    ForumMockUtilsMixin,
):
    """Tests for create_thread"""

    LONG_TITLE = (
        "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. "
        "Aenean commodo ligula eget dolor. Aenean massa. Cum sociis "
        "natoque penatibus et magnis dis parturient montes, nascetur "
        "ridiculus mus. Donec quam felis, ultricies nec, "
        "pellentesque eu, pretium quis, sem. Nulla consequat massa "
        "quis enim. Donec pede justo, fringilla vel, aliquet nec, "
        "vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet "
        "a, venenatis vitae, justo. Nullam dictum felis eu pede "
        "mollis pretium. Integer tincidunt. Cras dapibus. Vivamus "
        "elementum semper nisi. Aenean vulputate eleifend tellus. "
        "Aenean leo ligula, porttitor eu, consequat vitae, eleifend "
        "ac, enim. Aliquam lorem ante, dapibus in, viverra quis, "
        "feugiat a, tellus. Phasellus viverra nulla ut metus varius "
        "laoreet. Quisque rutrum. Aenean imperdiet. Etiam ultricies "
        "nisi vel augue. Curabitur ullamcorper ultricies nisi. Nam "
        "eget dui. Etiam rhoncus. Maecenas tempus, tellus eget "
        "condimentum rhoncus, sem quam semper libero, sit amet "
        "adipiscing sem neque sed ipsum. Nam quam nunc, blandit vel, "
        "luctus pulvinar, hendrerit id, lorem. Maecenas nec odio et "
        "ante tincidunt tempus. Donec vitae sapien ut libero "
        "venenatis faucibus. Nullam quis ante. Etiam sit amet orci "
        "eget eros faucibus tincidunt. Duis leo. Sed fringilla "
        "mauris sit amet nibh. Donec sodales sagittis magna. Sed "
        "consequat, leo eget bibendum sodales, augue velit cursus "
        "nunc, quis gravida magna mi a libero. Fusce vulputate "
        "eleifend sapien. Vestibulum purus quam, scelerisque ut, "
        "mollis sed, nonummy id, metus. Nullam accumsan lorem in "
        "dui. Cras ultricies mi eu turpis hendrerit fringilla. "
        "Vestibulum ante ipsum primis in faucibus orci luctus et "
        "ultrices posuere cubilia Curae; In ac dui quis mi "
        "consectetuer lacinia. Nam pretium turpis et arcu. Duis arcu "
        "tortor, suscipit eget, imperdiet nec, imperdiet iaculis, "
        "ipsum. Sed aliquam ultrices mauris. Integer ante arcu, "
        "accumsan a, consectetuer eget, posuere ut, mauris. Praesent "
        "adipiscing. Phasellus ullamcorper ipsum rutrum nunc. Nunc "
        "nonummy metus."
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        super().tearDownClass()
        super().disposeForumMocks()

    @mock.patch.dict(
        "django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True}
    )
    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.reset)
        self.addCleanup(httpretty.disable)
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.minimal_data = {
            "course_id": str(self.course.id),
            "topic_id": "test_topic",
            "type": "discussion",
            "title": "Test Title",
            "raw_body": "Test body",
        }

    def test_abuse_flagged(self):
        self.register_post_thread_response(
            {"id": "test_id", "username": self.user.username}
        )
        self.register_thread_flag_response("test_id")
        data = self.minimal_data.copy()
        data["abuse_flagged"] = "True"
        result = create_thread(self.request, data)
        assert result["abuse_flagged"] is True

        self.check_mock_called("update_thread_flag")
        params = {
            "thread_id": "test_id",
            "action": "flag",
            "user_id": "1",
            "course_id": str(self.course.id),
        }
        self.check_mock_called_with("update_thread_flag", -1, **params)


@ddt.ddt
@disable_signal(api, "comment_created")
@disable_signal(api, "comment_voted")
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
@mock.patch(
    "lms.djangoapps.discussion.signals.handlers.send_response_notifications",
    new=mock.Mock(),
)
class CreateCommentTest(
    ForumsEnableMixin,
    UrlResetMixin,
    SharedModuleStoreTestCase,
    MockSignalHandlerMixin,
    ForumMockUtilsMixin,
):
    """Tests for create_comment"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()
        cls.course = CourseFactory.create()

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        super().tearDownClass()
        super().disposeForumMocks()

    @mock.patch.dict(
        "django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True}
    )
    def setUp(self):
        super().setUp()
        httpretty.reset()
        httpretty.enable()
        self.course = CourseFactory.create()
        self.addCleanup(httpretty.reset)
        self.addCleanup(httpretty.disable)
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.register_get_thread_response(
            make_minimal_cs_thread(
                {
                    "id": "test_thread",
                    "course_id": str(self.course.id),
                    "commentable_id": "test_topic",
                }
            )
        )
        self.minimal_data = {
            "thread_id": "test_thread",
            "raw_body": "Test body",
        }

        mock_response = {
            "collection": [],
            "page": 1,
            "num_pages": 1,
            "subscriptions_count": 1,
            "corrected_text": None,
        }
        self.register_get_subscriptions("cohort_thread", mock_response)
        self.register_get_subscriptions("test_thread", mock_response)

    def test_abuse_flagged(self):
        self.register_post_comment_response(
            {"id": "test_comment", "username": self.user.username}, "test_thread"
        )
        self.register_comment_flag_response("test_comment")
        data = self.minimal_data.copy()
        data["abuse_flagged"] = "True"
        result = create_comment(self.request, data)
        assert result["abuse_flagged"] is True

        self.check_mock_called("update_comment_flag")
        params = {
            "comment_id": "test_comment",
            "action": "flag",
            "user_id": "1",
            "course_id": str(self.course.id),
        }
        self.check_mock_called_with("update_comment_flag", -1, **params)


@ddt.ddt
@disable_signal(api, "thread_edited")
@disable_signal(api, "thread_voted")
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class UpdateThreadTest(
    ForumsEnableMixin,
    UrlResetMixin,
    SharedModuleStoreTestCase,
    MockSignalHandlerMixin,
    ForumMockUtilsMixin,
):
    """Tests for update_thread"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()
        cls.course = CourseFactory.create()

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        super().tearDownClass()
        super().disposeForumMocks()

    @mock.patch.dict(
        "django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True}
    )
    def setUp(self):
        super().setUp()

        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.reset)
        self.addCleanup(httpretty.disable)
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

    def register_thread(self, overrides=None):
        """
        Make a thread with appropriate data overridden by the overrides
        parameter and register mock responses for both GET and PUT on its
        endpoint.
        """
        cs_data = make_minimal_cs_thread(
            {
                "id": "test_thread",
                "course_id": str(self.course.id),
                "commentable_id": "original_topic",
                "username": self.user.username,
                "user_id": str(self.user.id),
                "thread_type": "discussion",
                "title": "Original Title",
                "body": "Original body",
            }
        )
        cs_data.update(overrides or {})
        self.register_get_thread_response(cs_data)
        self.register_put_thread_response(cs_data)

    @ddt.data(*itertools.product([True, False], [True, False]))
    @ddt.unpack
    @mock.patch("eventtracking.tracker.emit")
    def test_abuse_flagged(self, old_flagged, new_flagged, mock_emit):
        """
        Test attempts to edit the "abuse_flagged" field.

        old_flagged indicates whether the thread should be flagged at the start
        of the test. new_flagged indicates the value for the "abuse_flagged"
        field in the update. If old_flagged and new_flagged are the same, no
        update should be made. Otherwise, a PUT should be made to the flag or
        or unflag endpoint according to the new_flagged value.
        """
        self.register_get_user_response(self.user)
        self.register_thread_flag_response("test_thread")
        self.register_thread(
            {"abuse_flaggers": [str(self.user.id)] if old_flagged else []}
        )
        data = {"abuse_flagged": new_flagged}
        result = update_thread(self.request, "test_thread", data)
        assert result["abuse_flagged"] == new_flagged

        flag_func_calls = self.get_mock_func_calls("update_thread_flag")
        last_function_args = flag_func_calls[-1] if flag_func_calls else None

        if old_flagged == new_flagged:
            assert last_function_args is None
        else:
            assert last_function_args[1]["action"] == (
                "flag" if new_flagged else "unflag"
            )
            params = {
                "thread_id": "test_thread",
                "action": "flag" if new_flagged else "unflag",
                "user_id": "1",
                "course_id": str(self.course.id),
            }
            if not new_flagged:
                params["update_all"] = False
            self.check_mock_called_with("update_thread_flag", -1, **params)

            expected_event_name = (
                "edx.forum.thread.reported"
                if new_flagged
                else "edx.forum.thread.unreported"
            )
            expected_event_data = {
                "body": "Original body",
                "id": "test_thread",
                "content_type": "Post",
                "commentable_id": "original_topic",
                "url": "",
                "user_course_roles": [],
                "user_forums_roles": [FORUM_ROLE_STUDENT],
                "target_username": self.user.username,
                "title_truncated": False,
                "title": "Original Title",
                "thread_type": "discussion",
                "group_id": None,
                "truncated": False,
            }
            if not new_flagged:
                expected_event_data["reported_status_cleared"] = False

            actual_event_name, actual_event_data = mock_emit.call_args[0]
            self.assertEqual(actual_event_name, expected_event_name)
            self.assertEqual(actual_event_data, expected_event_data)

    @ddt.data(
        (False, True),
        (True, True),
    )
    @ddt.unpack
    @mock.patch("eventtracking.tracker.emit")
    def test_thread_un_abuse_flag_for_moderator_role(
        self, is_author, remove_all, mock_emit
    ):
        """
        Test un-abuse flag for moderator role.

        When moderator unflags a reported thread, it should
        pass the "all" flag to the api. This will indicate
        to the api to clear all abuse_flaggers, and mark the
        thread as unreported.
        """
        _assign_role_to_user(
            user=self.user, course_id=self.course.id, role=FORUM_ROLE_ADMINISTRATOR
        )
        self.register_get_user_response(self.user)
        self.register_thread_flag_response("test_thread")
        self.register_thread(
            {
                "abuse_flaggers": ["11"],
                "user_id": str(self.user.id) if is_author else "12",
            }
        )
        data = {"abuse_flagged": False}
        update_thread(self.request, "test_thread", data)

        params = {
            "thread_id": "test_thread",
            "action": "unflag",
            "user_id": "1",
            "update_all": True if remove_all else False,
            "course_id": str(self.course.id),
        }

        self.check_mock_called_with("update_thread_flag", -1, **params)

        expected_event_name = "edx.forum.thread.unreported"
        expected_event_data = {
            "body": "Original body",
            "id": "test_thread",
            "content_type": "Post",
            "commentable_id": "original_topic",
            "url": "",
            "user_course_roles": [],
            "user_forums_roles": [FORUM_ROLE_STUDENT, FORUM_ROLE_ADMINISTRATOR],
            "target_username": self.user.username,
            "title_truncated": False,
            "title": "Original Title",
            "reported_status_cleared": False,
            "thread_type": "discussion",
            "group_id": None,
            "truncated": False,
        }

        actual_event_name, actual_event_data = mock_emit.call_args[0]
        self.assertEqual(actual_event_name, expected_event_name)
        self.assertEqual(actual_event_data, expected_event_data)


@ddt.ddt
@disable_signal(api, "comment_edited")
@disable_signal(api, "comment_voted")
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class UpdateCommentTest(
    ForumsEnableMixin,
    UrlResetMixin,
    SharedModuleStoreTestCase,
    MockSignalHandlerMixin,
    ForumMockUtilsMixin,
):
    """Tests for update_comment"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()
        cls.course = CourseFactory.create()

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        super().tearDownClass()
        super().disposeForumMocks()

    @mock.patch.dict(
        "django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True}
    )
    def setUp(self):
        super().setUp()

        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.reset)
        self.addCleanup(httpretty.disable)
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

    def register_comment(self, overrides=None, thread_overrides=None, course=None):
        """
        Make a comment with appropriate data overridden by the overrides
        parameter and register mock responses for both GET and PUT on its
        endpoint. Also mock GET for the related thread with thread_overrides.
        """
        if course is None:
            course = self.course

        cs_thread_data = make_minimal_cs_thread(
            {"id": "test_thread", "course_id": str(course.id)}
        )
        cs_thread_data.update(thread_overrides or {})
        self.register_get_thread_response(cs_thread_data)
        cs_comment_data = make_minimal_cs_comment(
            {
                "id": "test_comment",
                "course_id": cs_thread_data["course_id"],
                "thread_id": cs_thread_data["id"],
                "username": self.user.username,
                "user_id": str(self.user.id),
                "created_at": "2015-06-03T00:00:00Z",
                "updated_at": "2015-06-03T00:00:00Z",
                "body": "Original body",
            }
        )
        cs_comment_data.update(overrides or {})
        self.register_get_comment_response(cs_comment_data)
        self.register_put_comment_response(cs_comment_data)

    @ddt.data(*itertools.product([True, False], [True, False]))
    @ddt.unpack
    @mock.patch("eventtracking.tracker.emit")
    def test_abuse_flagged(self, old_flagged, new_flagged, mock_emit):
        """
        Test attempts to edit the "abuse_flagged" field.

        old_flagged indicates whether the comment should be flagged at the start
        of the test. new_flagged indicates the value for the "abuse_flagged"
        field in the update. If old_flagged and new_flagged are the same, no
        update should be made. Otherwise, a PUT should be made to the flag or
        or unflag endpoint according to the new_flagged value.
        """
        self.register_get_user_response(self.user)
        self.register_comment_flag_response("test_comment")
        self.register_comment(
            {"abuse_flaggers": [str(self.user.id)] if old_flagged else []}
        )
        data = {"abuse_flagged": new_flagged}
        result = update_comment(self.request, "test_comment", data)
        assert result["abuse_flagged"] == new_flagged
        flag_func_calls = self.get_mock_func_calls("update_comment_flag")
        last_function_args = flag_func_calls[-1] if flag_func_calls else None

        if old_flagged == new_flagged:
            assert last_function_args is None
        else:
            assert last_function_args[1]["action"] == (
                "flag" if new_flagged else "unflag"
            )
            params = {
                "comment_id": "test_comment",
                "action": "flag" if new_flagged else "unflag",
                "user_id": "1",
                "course_id": str(self.course.id),
            }
            if not new_flagged:
                params["update_all"] = False
            self.check_mock_called_with("update_comment_flag", -1, **params)

            expected_event_name = (
                "edx.forum.response.reported"
                if new_flagged
                else "edx.forum.response.unreported"
            )
            expected_event_data = {
                "body": "Original body",
                "id": "test_comment",
                "content_type": "Response",
                "commentable_id": "dummy",
                "url": "",
                "truncated": False,
                "user_course_roles": [],
                "user_forums_roles": [FORUM_ROLE_STUDENT],
                "target_username": self.user.username,
            }
            if not new_flagged:
                expected_event_data["reported_status_cleared"] = False

            actual_event_name, actual_event_data = mock_emit.call_args[0]
            self.assertEqual(actual_event_name, expected_event_name)
            self.assertEqual(actual_event_data, expected_event_data)

    @ddt.data(
        (False, True),
        (True, True),
    )
    @ddt.unpack
    @mock.patch("eventtracking.tracker.emit")
    def test_comment_un_abuse_flag_for_moderator_role(
        self, is_author, remove_all, mock_emit
    ):
        """
        Test un-abuse flag for moderator role.

        When moderator unflags a reported comment, it should
        pass the "all" flag to the api. This will indicate
        to the api to clear all abuse_flaggers, and mark the
        comment as unreported.
        """
        _assign_role_to_user(
            user=self.user, course_id=self.course.id, role=FORUM_ROLE_ADMINISTRATOR
        )
        self.register_get_user_response(self.user)
        self.register_comment_flag_response("test_comment")
        self.register_comment(
            {
                "abuse_flaggers": ["11"],
                "user_id": str(self.user.id) if is_author else "12",
            }
        )
        data = {"abuse_flagged": False}
        update_comment(self.request, "test_comment", data)

        params = {
            "comment_id": "test_comment",
            "action": "unflag",
            "user_id": "1",
            "update_all": True if remove_all else False,
            "course_id": str(self.course.id),
        }
        self.check_mock_called_with("update_comment_flag", -1, **params)

        expected_event_name = "edx.forum.response.unreported"
        expected_event_data = {
            "body": "Original body",
            "id": "test_comment",
            "content_type": "Response",
            "commentable_id": "dummy",
            "truncated": False,
            "url": "",
            "user_course_roles": [],
            "user_forums_roles": [FORUM_ROLE_STUDENT, FORUM_ROLE_ADMINISTRATOR],
            "target_username": self.user.username,
            "reported_status_cleared": False,
        }

        actual_event_name, actual_event_data = mock_emit.call_args[0]
        self.assertEqual(actual_event_name, expected_event_name)
        self.assertEqual(actual_event_data, expected_event_data)

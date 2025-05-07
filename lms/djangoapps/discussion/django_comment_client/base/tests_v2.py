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
from openedx_events.learning.signals import (
    FORUM_THREAD_CREATED,
    FORUM_THREAD_RESPONSE_CREATED,
    FORUM_RESPONSE_COMMENT_CREATED,
)

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.roles import CourseStaffRole, UserBasedRole
from common.djangoapps.student.tests.factories import (
    CourseAccessRoleFactory,
    CourseEnrollmentFactory,
    UserFactory,
)
from common.djangoapps.track.middleware import TrackMiddleware
from common.djangoapps.track.views import segmentio
from common.djangoapps.track.views.tests.base import (
    SEGMENTIO_TEST_USER_ID,
    SegmentIOTrackingTestCaseBase,
)
from common.djangoapps.util.testing import UrlResetMixin
from common.test.utils import MockSignalHandlerMixin, disable_signal
from lms.djangoapps.discussion.django_comment_client.base import views
from lms.djangoapps.discussion.django_comment_client.tests.group_id import (
    CohortedTopicGroupIdTestMixin,
    GroupIdAssertionMixin,
    NonCohortedTopicGroupIdTestMixin,
)
from lms.djangoapps.discussion.django_comment_client.tests.unicode import (
    UnicodeTestMixin,
)
from lms.djangoapps.discussion.django_comment_client.tests.utils import (
    CohortedTestCase,
    ForumsEnableMixin,
)
from lms.djangoapps.teams.tests.factories import (
    CourseTeamFactory,
    CourseTeamMembershipFactory,
)
from openedx.core.djangoapps.course_groups.cohorts import set_course_cohorted
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from openedx.core.djangoapps.django_comment_common.comment_client import Thread
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_STUDENT,
    CourseDiscussionSettings,
    Role,
    assign_role,
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
    TEST_DATA_SPLIT_MODULESTORE,
    ModuleStoreTestCase,
    SharedModuleStoreTestCase,
)
from xmodule.modulestore.tests.factories import (
    CourseFactory,
    BlockFactory,
    check_mongo_calls,
)

from .event_transformers import ForumThreadViewedEventTransformer
from lms.djangoapps.discussion.django_comment_client.tests.mixins import (
    MockForumApiMixin,
)


@disable_signal(views, "thread_edited")
@disable_signal(views, "thread_voted")
@disable_signal(views, "thread_deleted")
class ThreadActionGroupIdTestCase(
    CohortedTestCase, GroupIdAssertionMixin, MockForumApiMixin
):
    """Test case for thread actions with group ID assertions."""

    @classmethod
    def setUpClass(cls):
        """Set up class and forum mock."""
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        super().tearDownClass()
        super().disposeForumMocks()

    def call_view(
        self, view_name, mock_function, user=None, post_params=None, view_args=None
    ):
        """Call a view with the given parameters."""
        thread_response = {
            "user_id": str(self.student.id),
            "group_id": self.student_cohort.id,
            "closed": False,
            "type": "thread",
            "commentable_id": "non_team_dummy_id",
            "body": "test body",
        }

        self.set_mock_return_value("get_course_id_by_thread", self.course.id)
        self.set_mock_return_value("get_thread", thread_response)
        self.set_mock_return_value(mock_function, thread_response)

        request = RequestFactory().post("dummy_url", post_params or {})
        request.user = user or self.student
        request.view_name = view_name

        return getattr(views, view_name)(
            request,
            course_id=str(self.course.id),
            thread_id="dummy",
            **(view_args or {})
        )

    def test_pin_thread(self):
        """Test pinning a thread."""
        response = self.call_view("pin_thread", "pin_thread", user=self.moderator)
        assert response.status_code == 200
        self._assert_json_response_contains_group_info(response)

        response = self.call_view("un_pin_thread", "unpin_thread", user=self.moderator)
        assert response.status_code == 200
        self._assert_json_response_contains_group_info(response)


@disable_signal(views, "comment_endorsed")
class ViewPermissionsTestCase(
    ForumsEnableMixin,
    UrlResetMixin,
    SharedModuleStoreTestCase,
    MockForumApiMixin,
):
    """Test case for view permissions."""

    @classmethod
    def setUpClass(cls):  # pylint: disable=super-method-not-called
        """Set up class and forum mock."""
        super().setUpClassAndForumMock()

        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        super().tearDownClass()
        super().disposeForumMocks()

    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        super().setUpTestData()

        seed_permissions_roles(cls.course.id)

        cls.password = "test password"
        cls.student = UserFactory.create(password=cls.password)
        cls.moderator = UserFactory.create(password=cls.password)

        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)
        CourseEnrollmentFactory(user=cls.moderator, course_id=cls.course.id)

        cls.moderator.roles.add(
            Role.objects.get(name="Moderator", course_id=cls.course.id)
        )

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        """Set up the test case."""
        super().setUp()

        # Set return values dynamically using the mixin method
        self.set_mock_return_value("get_course_id_by_comment", self.course.id)
        self.set_mock_return_value("get_course_id_by_thread", self.course.id)
        self.set_mock_return_value("get_thread", {})
        self.set_mock_return_value("pin_thread", {})
        self.set_mock_return_value("unpin_thread", {})

    def test_pin_thread_as_student(self):
        """Test pinning a thread as a student."""
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse(
                "pin_thread",
                kwargs={"course_id": str(self.course.id), "thread_id": "dummy"},
            )
        )
        assert response.status_code == 401

    def test_pin_thread_as_moderator(self):
        """Test pinning a thread as a moderator."""
        self.client.login(username=self.moderator.username, password=self.password)
        response = self.client.post(
            reverse(
                "pin_thread",
                kwargs={"course_id": str(self.course.id), "thread_id": "dummy"},
            )
        )
        assert response.status_code == 200

    def test_un_pin_thread_as_student(self):
        """Test unpinning a thread as a student."""
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse(
                "un_pin_thread",
                kwargs={"course_id": str(self.course.id), "thread_id": "dummy"},
            )
        )
        assert response.status_code == 401

    def test_un_pin_thread_as_moderator(self):
        """Test unpinning a thread as a moderator."""
        self.client.login(username=self.moderator.username, password=self.password)
        response = self.client.post(
            reverse(
                "un_pin_thread",
                kwargs={"course_id": str(self.course.id), "thread_id": "dummy"},
            )
        )
        assert response.status_code == 200

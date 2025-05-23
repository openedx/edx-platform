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

from lms.djangoapps.discussion.tests.utils import (
    make_minimal_cs_thread,
    make_minimal_cs_comment,
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
        thread_response = make_minimal_cs_thread(
            {"user_id": str(self.student.id), "group_id": self.student_cohort.id}
        )

        self.set_mock_return_value("get_course_id_by_thread", str(self.course.id))
        self.set_mock_return_value("get_thread", thread_response)
        self.set_mock_return_value(mock_function, thread_response)

        request = RequestFactory().post("dummy_url", post_params or {})
        request.user = user or self.student
        request.view_name = view_name

        return getattr(views, view_name)(
            request,
            course_id=str(self.course.id),
            thread_id="dummy",
            **(view_args or {}),
        )

    def test_flag(self):
        with mock.patch(
            "openedx.core.djangoapps.django_comment_common.signals.thread_flagged.send"
        ) as signal_mock:
            response = self.call_view("flag_abuse_for_thread", "update_thread_flag")
            self._assert_json_response_contains_group_info(response)
            self.assertEqual(signal_mock.call_count, 1)
        response = self.call_view("un_flag_abuse_for_thread", "update_thread_flag")
        self._assert_json_response_contains_group_info(response)

    def test_pin_thread(self):
        """Test pinning a thread."""
        response = self.call_view("pin_thread", "pin_thread", user=self.moderator)
        assert response.status_code == 200
        self._assert_json_response_contains_group_info(response)

        response = self.call_view("un_pin_thread", "unpin_thread", user=self.moderator)
        assert response.status_code == 200
        self._assert_json_response_contains_group_info(response)

    def test_vote(self):
        response = self.call_view(
            "vote_for_thread", "update_thread_votes", view_args={"value": "up"}
        )
        self._assert_json_response_contains_group_info(response)
        response = self.call_view("undo_vote_for_thread", "delete_thread_vote")
        self._assert_json_response_contains_group_info(response)


class ViewsTestCaseMixin:

    def set_up_course(self, block_count=0):
        """
        Creates a course, optionally with block_count discussion blocks, and
        a user with appropriate permissions.
        """

        # create a course
        self.course = CourseFactory.create(
            org="MITx",
            course="999",
            discussion_topics={"Some Topic": {"id": "some_topic"}},
            display_name="Robot Super Course",
        )
        self.course_id = self.course.id

        # add some discussion blocks
        for i in range(block_count):
            BlockFactory.create(
                parent_location=self.course.location,
                category="discussion",
                discussion_id=f"id_module_{i}",
                discussion_category=f"Category {i}",
                discussion_target=f"Discussion {i}",
            )

        # seed the forums permissions and roles
        call_command("seed_permissions_roles", str(self.course_id))

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch("common.djangoapps.student.models.user.cc.User.save"):
            uname = "student"
            email = "student@edx.org"
            self.password = "Password1234"

            # Create the user and make them active so we can log them in.
            self.student = UserFactory.create(
                username=uname, email=email, password=self.password
            )
            self.student.is_active = True
            self.student.save()

            # Add a discussion moderator
            self.moderator = UserFactory.create(password=self.password)

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student, course_id=self.course_id)

            # Enroll the moderator and give them the appropriate roles
            CourseEnrollmentFactory(user=self.moderator, course_id=self.course.id)
            self.moderator.roles.add(
                Role.objects.get(name="Moderator", course_id=self.course.id)
            )

            assert self.client.login(username="student", password=self.password)

    def _setup_mock_request(self, mock_function, include_depth=False):
        """
        Ensure that mock_request returns the data necessary to make views
        function correctly
        """
        data = {
            "user_id": str(self.student.id),
            "closed": False,
            "commentable_id": "non_team_dummy_id",
            "thread_id": "dummy",
            "thread_type": "discussion",
        }
        if include_depth:
            data["depth"] = 0
        self.set_mock_return_value(mock_function, data)


@ddt.ddt
@disable_signal(views, "comment_flagged")
@disable_signal(views, "thread_flagged")
class ViewsTestCase(
    ForumsEnableMixin,
    MockForumApiMixin,
    UrlResetMixin,
    SharedModuleStoreTestCase,
    ViewsTestCaseMixin,
    MockSignalHandlerMixin,
):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        super().setUpClassAndForumMock()
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create(
                org="MITx",
                course="999",
                discussion_topics={"Some Topic": {"id": "some_topic"}},
                display_name="Robot Super Course",
            )

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        super().tearDownClass()
        super().disposeForumMocks()

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
        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch("common.djangoapps.student.models.user.cc.User.save"):
            uname = "student"
            email = "student@edx.org"
            self.password = "Password1234"

            # Create the user and make them active so we can log them in.
            self.student = UserFactory.create(
                username=uname, email=email, password=self.password
            )
            self.student.is_active = True
            self.student.save()

            # Add a discussion moderator
            self.moderator = UserFactory.create(password=self.password)

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student, course_id=self.course_id)

            # Enroll the moderator and give them the appropriate roles
            CourseEnrollmentFactory(user=self.moderator, course_id=self.course.id)
            self.moderator.roles.add(
                Role.objects.get(name="Moderator", course_id=self.course.id)
            )

            assert self.client.login(username="student", password=self.password)

        self.set_mock_return_value("get_course_id_by_thread", str(self.course.id))
        self.set_mock_return_value("get_course_id_by_comment", str(self.course.id))

    @contextmanager
    def assert_discussion_signals(self, signal, user=None):
        if user is None:
            user = self.student
        with self.assert_signal_sent(
            views, signal, sender=None, user=user, exclude_args=("post",)
        ):
            yield

    def test_flag_thread_open(self):
        self.flag_thread(False)

    def test_flag_thread_close(self):
        self.flag_thread(True)

    def flag_thread(self, is_closed):
        thread_data = make_minimal_cs_thread(
            {
                "id": "518d4237b023791dca00000d",
                "course_id": str(self.course_id),
                "closed": is_closed,
                "user_id": "1",
                "username": "robot",
                "abuse_flaggers": [1],
            }
        )
        self.set_mock_return_value("get_thread", thread_data)
        self.set_mock_return_value("update_thread_flag", thread_data)
        url = reverse(
            "flag_abuse_for_thread",
            kwargs={
                "thread_id": "518d4237b023791dca00000d",
                "course_id": str(self.course_id),
            },
        )
        response = self.client.post(url)
        self.check_mock_called("update_thread_flag")

        self.check_mock_called_with(
            "get_thread",
            0,
            thread_id="518d4237b023791dca00000d",
            params={
                "mark_as_read": True,
                "with_responses": False,
                "reverse_order": False,
                "merge_question_type_responses": False,
            },
            course_id=str(self.course_id),
        )

        self.check_mock_called_with(
            "update_thread_flag",
            0,
            thread_id="518d4237b023791dca00000d",
            action="flag",
            user_id=ANY,
            course_id=str(self.course_id),
        )

        self.check_mock_called_with(
            "get_thread",
            1,
            thread_id="518d4237b023791dca00000d",
            params={
                "mark_as_read": True,
                "with_responses": False,
                "reverse_order": False,
                "merge_question_type_responses": False,
            },
            course_id=str(self.course_id),
        )

        assert response.status_code == 200

    def test_un_flag_thread_open(self):
        self.un_flag_thread(False)

    def test_un_flag_thread_close(self):
        self.un_flag_thread(True)

    def un_flag_thread(self, is_closed):
        thread_data = make_minimal_cs_thread(
            {
                "id": "518d4237b023791dca00000d",
                "course_id": str(self.course_id),
                "closed": is_closed,
                "user_id": "1",
                "username": "robot",
                "abuse_flaggers": [1],
            }
        )

        self.set_mock_return_value("get_thread", thread_data)
        self.set_mock_return_value("update_thread_flag", thread_data)
        url = reverse(
            "un_flag_abuse_for_thread",
            kwargs={
                "thread_id": "518d4237b023791dca00000d",
                "course_id": str(self.course_id),
            },
        )
        response = self.client.post(url)
        self.check_mock_called("update_thread_flag")

        self.check_mock_called_with(
            "get_thread",
            0,
            thread_id="518d4237b023791dca00000d",
            params={
                "mark_as_read": True,
                "with_responses": False,
                "reverse_order": False,
                "merge_question_type_responses": False,
            },
            course_id=str(self.course_id),
        )

        self.check_mock_called_with(
            "update_thread_flag",
            0,
            thread_id="518d4237b023791dca00000d",
            action="unflag",
            user_id=ANY,
            update_all=False,
            course_id=str(self.course_id),
        )

        self.check_mock_called_with(
            "get_thread",
            1,
            thread_id="518d4237b023791dca00000d",
            params={
                "mark_as_read": True,
                "with_responses": False,
                "reverse_order": False,
                "merge_question_type_responses": False,
            },
            course_id=str(self.course_id),
        )

        assert response.status_code == 200

    def test_flag_comment_open(self):
        self.flag_comment(False)

    def test_flag_comment_close(self):
        self.flag_comment(True)

    def flag_comment(self, is_closed):
        comment_data = make_minimal_cs_comment(
            {
                "id": "518d4237b023791dca00000d",
                "body": "this is a comment",
                "course_id": str(self.course_id),
                "closed": is_closed,
                "user_id": "1",
                "username": "robot",
                "abuse_flaggers": [1],
            }
        )

        self.set_mock_return_value("get_parent_comment", comment_data)
        self.set_mock_return_value("update_comment_flag", comment_data)
        url = reverse(
            "flag_abuse_for_comment",
            kwargs={
                "comment_id": "518d4237b023791dca00000d",
                "course_id": str(self.course_id),
            },
        )

        response = self.client.post(url)
        self.check_mock_called("update_thread_flag")

        self.check_mock_called_with(
            "get_parent_comment",
            0,
            comment_id="518d4237b023791dca00000d",
            course_id=str(self.course_id),
        )

        self.check_mock_called_with(
            "update_comment_flag",
            0,
            comment_id="518d4237b023791dca00000d",
            action="flag",
            user_id=ANY,
            course_id=str(self.course_id),
        )

        self.check_mock_called_with(
            "get_parent_comment",
            1,
            comment_id="518d4237b023791dca00000d",
            course_id=str(self.course_id),
        )

        assert response.status_code == 200

    def test_un_flag_comment_open(self):
        self.un_flag_comment(False)

    def test_un_flag_comment_close(self):
        self.un_flag_comment(True)

    def un_flag_comment(self, is_closed):
        comment_data = make_minimal_cs_comment(
            {
                "id": "518d4237b023791dca00000d",
                "body": "this is a comment",
                "course_id": str(self.course_id),
                "closed": is_closed,
                "user_id": "1",
                "username": "robot",
                "abuse_flaggers": [],
            }
        )

        self.set_mock_return_value("get_parent_comment", comment_data)
        self.set_mock_return_value("update_comment_flag", comment_data)
        url = reverse(
            "un_flag_abuse_for_comment",
            kwargs={
                "comment_id": "518d4237b023791dca00000d",
                "course_id": str(self.course_id),
            },
        )

        response = self.client.post(url)
        self.check_mock_called("update_thread_flag")

        self.check_mock_called_with(
            "get_parent_comment",
            0,
            comment_id="518d4237b023791dca00000d",
            course_id=str(self.course_id),
        )

        self.check_mock_called_with(
            "update_comment_flag",
            0,
            comment_id="518d4237b023791dca00000d",
            action="unflag",
            update_all=False,
            user_id=ANY,
            course_id=str(self.course_id),
        )

        self.check_mock_called_with(
            "get_parent_comment",
            1,
            comment_id="518d4237b023791dca00000d",
            course_id=str(self.course_id),
        )

        assert response.status_code == 200

    @ddt.data(
        ("upvote_thread", "update_thread_votes", "thread_id", "thread_voted"),
        ("upvote_comment", "update_comment_votes", "comment_id", "comment_voted"),
        ("downvote_thread", "update_thread_votes", "thread_id", "thread_voted"),
        ("downvote_comment", "update_comment_votes", "comment_id", "comment_voted"),
    )
    @ddt.unpack
    def test_voting(self, view_name, function_name, item_id, signal):
        self._setup_mock_request("get_thread")
        self._setup_mock_request("get_parent_comment")
        self._setup_mock_request(function_name)
        with self.assert_discussion_signals(signal):
            response = self.client.post(
                reverse(
                    view_name,
                    kwargs={item_id: "dummy", "course_id": str(self.course_id)},
                )
            )
        assert response.status_code == 200


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


class CommentActionTestCase(CohortedTestCase, MockForumApiMixin):
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
        comment_response = make_minimal_cs_comment(
            {"user_id": str(self.student.id), "group_id": self.student_cohort.id}
        )

        self.set_mock_return_value("get_course_id_by_comment", str(self.course.id))
        self.set_mock_return_value("get_parent_comment", comment_response)
        self.set_mock_return_value(mock_function, comment_response)

        request = RequestFactory().post("dummy_url", post_params or {})
        request.user = user or self.student
        request.view_name = view_name

        return getattr(views, view_name)(
            request,
            course_id=str(self.course.id),
            comment_id="dummy",
            **(view_args or {}),
        )

    def test_flag(self):
        with mock.patch(
            "openedx.core.djangoapps.django_comment_common.signals.comment_flagged.send"
        ) as signal_mock:
            self.call_view("flag_abuse_for_comment", "update_comment_flag")
            self.assertEqual(signal_mock.call_count, 1)


@ddt.ddt
@disable_signal(views, "thread_voted")
@disable_signal(views, "thread_edited")
@disable_signal(views, "comment_created")
@disable_signal(views, "comment_voted")
@disable_signal(views, "comment_deleted")
@disable_signal(views, "comment_flagged")
@disable_signal(views, "thread_flagged")
class TeamsPermissionsTestCase(
    UrlResetMixin, SharedModuleStoreTestCase, MockForumApiMixin
):
    # Most of the test points use the same ddt data.
    # args: user, commentable_id, status_code
    ddt_permissions_args = [
        # Student in team can do operations on threads/comments within the team commentable.
        ("student_in_team", "team_commentable_id", 200),
        # Non-team commentables can be edited by any student.
        ("student_in_team", "course_commentable_id", 200),
        # Student not in team cannot do operations within the team commentable.
        ("student_not_in_team", "team_commentable_id", 401),
        # Non-team commentables can be edited by any student.
        ("student_not_in_team", "course_commentable_id", 200),
        # Moderators can always operator on threads within a team, regardless of team membership.
        ("moderator", "team_commentable_id", 200),
        # Group moderators have regular student privileges for creating a thread and commenting
        ("group_moderator", "course_commentable_id", 200),
    ]

    def change_divided_discussion_settings(self, scheme):
        """
        Change divided discussion settings for the current course.
        If dividing by cohorts, create and assign users to a cohort.
        """
        enable_cohorts = True if scheme is CourseDiscussionSettings.COHORT else False
        discussion_settings = CourseDiscussionSettings.get(self.course.id)
        discussion_settings.update(
            {
                "enable_cohorts": enable_cohorts,
                "divided_discussions": [],
                "always_divide_inline_discussions": True,
                "division_scheme": scheme,
            }
        )
        set_course_cohorted(self.course.id, enable_cohorts)

    @classmethod
    def setUpClass(cls):
        super().setUpClassAndForumMock()
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            teams_config_data = {
                "topics": [
                    {
                        "id": "topic_id",
                        "name": "Solar Power",
                        "description": "Solar power is hot",
                    }
                ]
            }
            cls.course = CourseFactory.create(
                teams_configuration=TeamsConfig(teams_config_data)
            )

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        super().tearDownClass()
        super().disposeForumMocks()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.password = "test password"
        seed_permissions_roles(cls.course.id)

        # Create enrollment tracks
        CourseModeFactory.create(course_id=cls.course.id, mode_slug=CourseMode.VERIFIED)
        CourseModeFactory.create(course_id=cls.course.id, mode_slug=CourseMode.AUDIT)

        # Create 6 users--
        # student in team (in the team, audit)
        # student not in team (not in the team, audit)
        # cohorted (in the cohort, audit)
        # verified (not in the cohort, verified)
        # moderator (in the cohort, audit, moderator permissions)
        # group moderator (in the cohort, verified, group moderator permissions)
        def create_users_and_enroll(coursemode):
            student = UserFactory.create(password=cls.password)
            CourseEnrollmentFactory(
                course_id=cls.course.id, user=student, mode=coursemode
            )
            return student

        cls.student_in_team, cls.student_not_in_team, cls.moderator, cls.cohorted = [
            create_users_and_enroll(CourseMode.AUDIT) for _ in range(4)
        ]
        cls.verified, cls.group_moderator = [
            create_users_and_enroll(CourseMode.VERIFIED) for _ in range(2)
        ]

        # Give moderator and group moderator permissions
        cls.moderator.roles.add(
            Role.objects.get(name="Moderator", course_id=cls.course.id)
        )
        assign_role(cls.course.id, cls.group_moderator, "Group Moderator")

        # Create a team
        cls.team_commentable_id = "team_discussion_id"
        cls.team = CourseTeamFactory.create(
            name="The Only Team",
            course_id=cls.course.id,
            topic_id="topic_id",
            discussion_topic_id=cls.team_commentable_id,
        )
        CourseTeamMembershipFactory.create(team=cls.team, user=cls.student_in_team)

        # Dummy commentable ID not linked to a team
        cls.course_commentable_id = "course_level_commentable"

        # Create cohort and add students to it
        CohortFactory(
            course_id=cls.course.id,
            name="Test Cohort",
            users=[cls.group_moderator, cls.cohorted],
        )

    @mock.patch.dict(
        "django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True}
    )
    def setUp(self):
        super().setUp()

    def _setup_mock(self, user, mock_functions=[], data=None):
        user = getattr(self, user)
        mock_functions = mock_functions or []
        for mock_func in mock_functions:
            self.set_mock_return_value(mock_func, data or {})
        self.client.login(username=user.username, password=self.password)

    @ddt.data(*ddt_permissions_args)
    @ddt.unpack
    def test_comment_actions(self, user, commentable_id, status_code):
        """
        Verify that voting and flagging of comments is limited to members of the team or users with
        'edit_content' permission.
        """
        commentable_id = getattr(self, commentable_id)
        self._setup_mock(
            user,
            [
                "get_parent_comment",
                "update_comment_flag",
                "update_comment_votes",
                "delete_comment_vote",
            ],
            make_minimal_cs_comment(
                {
                    "closed": False,
                    "commentable_id": commentable_id,
                    "course_id": str(self.course.id),
                }
            ),
        )
        # "un_flag_abuse_for_comment", "flag_abuse_for_comment",
        for action in ["upvote_comment", "downvote_comment"]:
            response = self.client.post(
                reverse(
                    action,
                    kwargs={
                        "course_id": str(self.course.id),
                        "comment_id": "dummy",
                    },
                )
            )
            assert response.status_code == status_code

    @ddt.data(*ddt_permissions_args)
    @ddt.unpack
    def test_threads_actions(self, user, commentable_id, status_code):
        """
        Verify that voting, flagging, and following of threads is limited to members of the team or users with
        'edit_content' permission.
        """
        commentable_id = getattr(self, commentable_id)
        self._setup_mock(
            user,
            [
                "get_thread",
                "update_thread_flag",
                "update_thread_votes",
                "delete_thread_vote",
            ],
            make_minimal_cs_thread(
                {
                    "commentable_id": commentable_id,
                    "course_id": str(self.course.id),
                }
            ),
        )

        for action in [
            "un_flag_abuse_for_thread",
            "flag_abuse_for_thread",
            "upvote_thread",
            "downvote_thread",
        ]:
            response = self.client.post(
                reverse(
                    action,
                    kwargs={
                        "course_id": str(self.course.id),
                        "thread_id": "dummy",
                    },
                )
            )
            assert response.status_code == status_code


@disable_signal(views, "comment_created")
@ddt.ddt
class ForumEventTestCase(
    ForumsEnableMixin, SharedModuleStoreTestCase, MockForumApiMixin
):
    """
    Forum actions are expected to launch analytics events. Test these here.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClassAndForumMock()
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        super().tearDownClass()
        super().disposeForumMocks()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        seed_permissions_roles(cls.course.id)

        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)
        cls.student.roles.add(Role.objects.get(name="Student", course_id=cls.course.id))
        CourseAccessRoleFactory(
            course_id=cls.course.id, user=cls.student, role="Wizard"
        )

    @ddt.data(
        ("vote_for_thread", "update_thread_votes", "thread_id", "thread"),
        ("undo_vote_for_thread", "delete_thread_vote", "thread_id", "thread"),
        ("vote_for_comment", "update_comment_votes", "comment_id", "response"),
        ("undo_vote_for_comment", "delete_comment_vote", "comment_id", "response"),
    )
    @ddt.unpack
    @patch("eventtracking.tracker.emit")
    def test_thread_voted_event(
        self, view_name, function_name, obj_id_name, obj_type, mock_emit
    ):
        undo = view_name.startswith("undo")
        cs_thread = make_minimal_cs_thread(
            {
                "commentable_id": "test_commentable_id",
                "username": "gumprecht",
            }
        )
        cs_comment = make_minimal_cs_comment(
            {
                "closed": False,
                "commentable_id": "test_commentable_id",
                "username": "gumprecht",
            }
        )
        self.set_mock_return_value("get_thread", cs_thread)
        self.set_mock_return_value("get_parent_comment", cs_comment)
        self.set_mock_return_value(
            function_name, cs_thread if "thread" in view_name else cs_comment
        )

        request = RequestFactory().post("dummy_url", {})
        request.user = self.student
        request.view_name = view_name
        view_function = getattr(views, view_name)
        kwargs = dict(course_id=str(self.course.id))
        kwargs[obj_id_name] = obj_id_name
        if not undo:
            kwargs.update(value="up")
        view_function(request, **kwargs)

        assert mock_emit.called
        event_name, event = mock_emit.call_args[0]
        assert event_name == f"edx.forum.{obj_type}.voted"
        assert event["target_username"] == "gumprecht"
        assert event["undo_vote"] == undo
        assert event["vote_value"] == "up"

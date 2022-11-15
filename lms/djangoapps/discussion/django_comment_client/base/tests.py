import pytest
# pylint: skip-file
"""Tests for django comment client views."""


import json
import logging
from contextlib import contextmanager

import ddt
import mock
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test.client import RequestFactory
from django.urls import reverse
from eventtracking.processors.exceptions import EventEmissionExit
from mock import ANY, Mock, patch
from opaque_keys.edx.keys import CourseKey

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
from lms.djangoapps.discussion.django_comment_client.tests.group_id import (
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
    TEST_DATA_MONGO_AMNESTY_MODULESTORE, ModuleStoreTestCase, SharedModuleStoreTestCase,
)
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

from .event_transformers import ForumThreadViewedEventTransformer

log = logging.getLogger(__name__)

CS_PREFIX = "http://localhost:4567/api/v1"

QUERY_COUNT_TABLE_IGNORELIST = WAFFLE_TABLES

# pylint: disable=missing-docstring


class MockRequestSetupMixin:
    def _create_response_mock(self, data):
        return Mock(
            text=json.dumps(data),
            json=Mock(return_value=data),
            status_code=200
        )

    def _set_mock_request_data(self, mock_request, data):
        mock_request.return_value = self._create_response_mock(data)


@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
class CreateThreadGroupIdTestCase(
        MockRequestSetupMixin,
        CohortedTestCase,
        CohortedTopicGroupIdTestMixin,
        NonCohortedTopicGroupIdTestMixin
):
    cs_endpoint = "/threads"

    def call_view(self, mock_request, commentable_id, user, group_id, pass_group_id=True):
        self._set_mock_request_data(mock_request, {})
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

    def test_group_info_in_response(self, mock_request):
        response = self.call_view(
            mock_request,
            "cohorted_topic",
            self.student,
            ''
        )
        self._assert_json_response_contains_group_info(response)


@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
@disable_signal(views, 'thread_edited')
@disable_signal(views, 'thread_voted')
@disable_signal(views, 'thread_deleted')
class ThreadActionGroupIdTestCase(
        MockRequestSetupMixin,
        CohortedTestCase,
        GroupIdAssertionMixin
):
    def call_view(
            self,
            view_name,
            mock_request,
            user=None,
            post_params=None,
            view_args=None
    ):
        self._set_mock_request_data(
            mock_request,
            {
                "user_id": str(self.student.id),
                "group_id": self.student_cohort.id,
                "closed": False,
                "type": "thread",
                "commentable_id": "non_team_dummy_id",
                "body": "test body",
            }
        )
        request = RequestFactory().post("dummy_url", post_params or {})
        request.user = user or self.student
        request.view_name = view_name

        return getattr(views, view_name)(
            request,
            course_id=str(self.course.id),
            thread_id="dummy",
            **(view_args or {})
        )

    def test_update(self, mock_request):
        response = self.call_view(
            "update_thread",
            mock_request,
            post_params={"body": "body", "title": "title"}
        )
        self._assert_json_response_contains_group_info(response)

    def test_delete(self, mock_request):
        response = self.call_view("delete_thread", mock_request)
        self._assert_json_response_contains_group_info(response)

    def test_vote(self, mock_request):
        response = self.call_view(
            "vote_for_thread",
            mock_request,
            view_args={"value": "up"}
        )
        self._assert_json_response_contains_group_info(response)
        response = self.call_view("undo_vote_for_thread", mock_request)
        self._assert_json_response_contains_group_info(response)

    def test_flag(self, mock_request):
        response = self.call_view("flag_abuse_for_thread", mock_request)
        self._assert_json_response_contains_group_info(response)
        response = self.call_view("un_flag_abuse_for_thread", mock_request)
        self._assert_json_response_contains_group_info(response)

    def test_pin(self, mock_request):
        response = self.call_view(
            "pin_thread",
            mock_request,
            user=self.moderator
        )
        self._assert_json_response_contains_group_info(response)
        response = self.call_view(
            "un_pin_thread",
            mock_request,
            user=self.moderator
        )
        self._assert_json_response_contains_group_info(response)

    def test_openclose(self, mock_request):
        response = self.call_view(
            "openclose_thread",
            mock_request,
            user=self.moderator
        )
        self._assert_json_response_contains_group_info(
            response,
            lambda d: d['content']
        )


class ViewsTestCaseMixin:

    def set_up_course(self, module_count=0):
        """
        Creates a course, optionally with module_count discussion modules, and
        a user with appropriate permissions.
        """

        # create a course
        self.course = CourseFactory.create(
            org='MITx', course='999',
            discussion_topics={"Some Topic": {"id": "some_topic"}},
            display_name='Robot Super Course',
        )
        self.course_id = self.course.id

        # add some discussion modules
        for i in range(module_count):
            ItemFactory.create(
                parent_location=self.course.location,
                category='discussion',
                discussion_id=f'id_module_{i}',
                discussion_category=f'Category {i}',
                discussion_target=f'Discussion {i}'
            )

        # seed the forums permissions and roles
        call_command('seed_permissions_roles', str(self.course_id))

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('common.djangoapps.student.models.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            self.password = 'test'

            # Create the user and make them active so we can log them in.
            self.student = UserFactory.create(username=uname, email=email, password=self.password)
            self.student.is_active = True
            self.student.save()

            # Add a discussion moderator
            self.moderator = UserFactory.create(password=self.password)

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student,
                                    course_id=self.course_id)

            # Enroll the moderator and give them the appropriate roles
            CourseEnrollmentFactory(user=self.moderator, course_id=self.course.id)
            self.moderator.roles.add(Role.objects.get(name="Moderator", course_id=self.course.id))

            assert self.client.login(username='student', password=self.password)

    def _setup_mock_request(self, mock_request, include_depth=False):
        """
        Ensure that mock_request returns the data necessary to make views
        function correctly
        """
        data = {
            "user_id": str(self.student.id),
            "closed": False,
            "commentable_id": "non_team_dummy_id"
        }
        if include_depth:
            data["depth"] = 0
        self._set_mock_request_data(mock_request, data)

    def create_thread_helper(self, mock_request, extra_request_data=None, extra_response_data=None):
        """
        Issues a request to create a thread and verifies the result.
        """
        self._set_mock_request_data(mock_request, {
            "thread_type": "discussion",
            "title": "Hello",
            "body": "this is a post",
            "course_id": "MITx/999/Robot_Super_Course",
            "anonymous": False,
            "anonymous_to_peers": False,
            "commentable_id": "i4x-MITx-999-course-Robot_Super_Course",
            "created_at": "2013-05-10T18:53:43Z",
            "updated_at": "2013-05-10T18:53:43Z",
            "at_position_list": [],
            "closed": False,
            "id": "518d4237b023791dca00000d",
            "user_id": "1",
            "username": "robot",
            "votes": {
                "count": 0,
                "up_count": 0,
                "down_count": 0,
                "point": 0
            },
            "abuse_flaggers": [],
            "type": "thread",
            "group_id": None,
            "pinned": False,
            "endorsed": False,
            "unread_comments_count": 0,
            "read": False,
            "comments_count": 0,
        })
        thread = {
            "thread_type": "discussion",
            "body": ["this is a post"],
            "anonymous_to_peers": ["false"],
            "auto_subscribe": ["false"],
            "anonymous": ["false"],
            "title": ["Hello"],
        }
        if extra_request_data:
            thread.update(extra_request_data)
        url = reverse('create_thread', kwargs={'commentable_id': 'i4x-MITx-999-course-Robot_Super_Course',
                                               'course_id': str(self.course_id)})
        response = self.client.post(url, data=thread)
        assert mock_request.called
        expected_data = {
            'thread_type': 'discussion',
            'body': 'this is a post',
            'context': ThreadContext.COURSE,
            'anonymous_to_peers': False, 'user_id': 1,
            'title': 'Hello',
            'commentable_id': 'i4x-MITx-999-course-Robot_Super_Course',
            'anonymous': False,
            'course_id': str(self.course_id),
        }
        if extra_response_data:
            expected_data.update(extra_response_data)
        mock_request.assert_called_with(
            'post',
            f'{CS_PREFIX}/i4x-MITx-999-course-Robot_Super_Course/threads',
            data=expected_data,
            params={'request_id': ANY},
            headers=ANY,
            timeout=5
        )
        assert response.status_code == 200

    def update_thread_helper(self, mock_request):
        """
        Issues a request to update a thread and verifies the result.
        """
        self._setup_mock_request(mock_request)
        # Mock out saving in order to test that content is correctly
        # updated. Otherwise, the call to thread.save() receives the
        # same mocked request data that the original call to retrieve
        # the thread did, overwriting any changes.
        with patch.object(Thread, 'save'):
            response = self.client.post(
                reverse("update_thread", kwargs={
                    "thread_id": "dummy",
                    "course_id": str(self.course_id)
                }),
                data={"body": "foo", "title": "foo", "commentable_id": "some_topic"}
            )
        assert response.status_code == 200
        data = json.loads(response.content.decode('utf-8'))
        assert data['body'] == 'foo'
        assert data['title'] == 'foo'
        assert data['commentable_id'] == 'some_topic'


@ddt.ddt
@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
@disable_signal(views, 'thread_created')
@disable_signal(views, 'thread_edited')
class ViewsQueryCountTestCase(
        ForumsEnableMixin,
        UrlResetMixin,
        ModuleStoreTestCase,
        MockRequestSetupMixin,
        ViewsTestCaseMixin
):

    CREATE_USER = False
    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']
    ENABLED_SIGNALS = ['course_published']

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()

    def count_queries(func):  # pylint: disable=no-self-argument
        """
        Decorates test methods to count mongo and SQL calls for a
        particular modulestore.
        """
        def inner(self, default_store, module_count, mongo_calls, sql_queries, *args, **kwargs):
            with modulestore().default_store(default_store):
                self.set_up_course(module_count=module_count)
                self.clear_caches()
                with self.assertNumQueries(sql_queries, table_ignorelist=QUERY_COUNT_TABLE_IGNORELIST):
                    with check_mongo_calls(mongo_calls):
                        func(self, *args, **kwargs)
        return inner

    @ddt.data(
        (ModuleStoreEnum.Type.split, 3, 8, 42),
    )
    @ddt.unpack
    @count_queries
    def test_create_thread(self, mock_request):
        self.create_thread_helper(mock_request)

    @ddt.data(
        (ModuleStoreEnum.Type.split, 3, 6, 42),
    )
    @ddt.unpack
    @count_queries
    def test_update_thread(self, mock_request):
        self.update_thread_helper(mock_request)


@ddt.ddt
@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
class ViewsTestCase(
        ForumsEnableMixin,
        UrlResetMixin,
        SharedModuleStoreTestCase,
        MockRequestSetupMixin,
        ViewsTestCaseMixin,
        MockSignalHandlerMixin
):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create(
                org='MITx', course='999',
                discussion_topics={"Some Topic": {"id": "some_topic"}},
                display_name='Robot Super Course',
            )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.course_id = cls.course.id

        # seed the forums permissions and roles
        call_command('seed_permissions_roles', str(cls.course_id))

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        # Patching the ENABLE_DISCUSSION_SERVICE value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super().setUp()

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('common.djangoapps.student.models.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            self.password = 'test'

            # Create the user and make them active so we can log them in.
            self.student = UserFactory.create(username=uname, email=email, password=self.password)
            self.student.is_active = True
            self.student.save()

            # Add a discussion moderator
            self.moderator = UserFactory.create(password=self.password)

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student,
                                    course_id=self.course_id)

            # Enroll the moderator and give them the appropriate roles
            CourseEnrollmentFactory(user=self.moderator, course_id=self.course.id)
            self.moderator.roles.add(Role.objects.get(name="Moderator", course_id=self.course.id))

            assert self.client.login(username='student', password=self.password)

    @contextmanager
    def assert_discussion_signals(self, signal, user=None):
        if user is None:
            user = self.student
        with self.assert_signal_sent(views, signal, sender=None, user=user, exclude_args=('post',)):
            yield

    def test_create_thread(self, mock_request):
        with self.assert_discussion_signals('thread_created'):
            self.create_thread_helper(mock_request)

    def test_create_thread_standalone(self, mock_request):
        team = CourseTeamFactory.create(
            name="A Team",
            course_id=self.course_id,
            topic_id='topic_id',
            discussion_topic_id="i4x-MITx-999-course-Robot_Super_Course"
        )

        # Add the student to the team so they can post to the commentable.
        team.add_user(self.student)

        # create_thread_helper verifies that extra data are passed through to the comments service
        self.create_thread_helper(mock_request, extra_response_data={'context': ThreadContext.STANDALONE})

    @ddt.data(
        ('follow_thread', 'thread_followed'),
        ('unfollow_thread', 'thread_unfollowed'),
    )
    @ddt.unpack
    def test_follow_unfollow_thread_signals(self, view_name, signal, mock_request):
        self.create_thread_helper(mock_request)

        with self.assert_discussion_signals(signal):
            response = self.client.post(
                reverse(
                    view_name,
                    kwargs={"course_id": str(self.course_id), "thread_id": 'i4x-MITx-999-course-Robot_Super_Course'}
                )
            )
        assert response.status_code == 200

    def test_delete_thread(self, mock_request):
        self._set_mock_request_data(mock_request, {
            "user_id": str(self.student.id),
            "closed": False,
            "body": "test body",
        })
        test_thread_id = "test_thread_id"
        request = RequestFactory().post("dummy_url", {"id": test_thread_id})
        request.user = self.student
        request.view_name = "delete_thread"
        with self.assert_discussion_signals('thread_deleted'):
            response = views.delete_thread(
                request,
                course_id=str(self.course.id),
                thread_id=test_thread_id
            )
        assert response.status_code == 200
        assert mock_request.called

    def test_delete_comment(self, mock_request):
        self._set_mock_request_data(mock_request, {
            "user_id": str(self.student.id),
            "closed": False,
            "body": "test body",
        })
        test_comment_id = "test_comment_id"
        request = RequestFactory().post("dummy_url", {"id": test_comment_id})
        request.user = self.student
        request.view_name = "delete_comment"
        with self.assert_discussion_signals('comment_deleted'):
            response = views.delete_comment(
                request,
                course_id=str(self.course.id),
                comment_id=test_comment_id
            )
        assert response.status_code == 200
        assert mock_request.called
        args = mock_request.call_args[0]
        assert args[0] == 'delete'
        assert args[1].endswith(f"/{test_comment_id}")

    def _test_request_error(self, view_name, view_kwargs, data, mock_request):
        """
        Submit a request against the given view with the given data and ensure
        that the result is a 400 error and that no data was posted using
        mock_request
        """
        self._setup_mock_request(mock_request, include_depth=(view_name == "create_sub_comment"))

        response = self.client.post(reverse(view_name, kwargs=view_kwargs), data=data)
        assert response.status_code == 400
        for call in mock_request.call_args_list:
            assert call[0][0].lower() == 'get'

    def test_create_thread_no_title(self, mock_request):
        self._test_request_error(
            "create_thread",
            {"commentable_id": "dummy", "course_id": str(self.course_id)},
            {"body": "foo"},
            mock_request
        )

    def test_create_thread_empty_title(self, mock_request):
        self._test_request_error(
            "create_thread",
            {"commentable_id": "dummy", "course_id": str(self.course_id)},
            {"body": "foo", "title": " "},
            mock_request
        )

    def test_create_thread_no_body(self, mock_request):
        self._test_request_error(
            "create_thread",
            {"commentable_id": "dummy", "course_id": str(self.course_id)},
            {"title": "foo"},
            mock_request
        )

    def test_create_thread_empty_body(self, mock_request):
        self._test_request_error(
            "create_thread",
            {"commentable_id": "dummy", "course_id": str(self.course_id)},
            {"body": " ", "title": "foo"},
            mock_request
        )

    def test_update_thread_no_title(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": str(self.course_id)},
            {"body": "foo"},
            mock_request
        )

    def test_update_thread_empty_title(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": str(self.course_id)},
            {"body": "foo", "title": " "},
            mock_request
        )

    def test_update_thread_no_body(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": str(self.course_id)},
            {"title": "foo"},
            mock_request
        )

    def test_update_thread_empty_body(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": str(self.course_id)},
            {"body": " ", "title": "foo"},
            mock_request
        )

    def test_update_thread_course_topic(self, mock_request):
        with self.assert_discussion_signals('thread_edited'):
            self.update_thread_helper(mock_request)

    @patch(
        'lms.djangoapps.discussion.django_comment_client.utils.get_discussion_categories_ids',
        return_value=["test_commentable"],
    )
    def test_update_thread_wrong_commentable_id(self, mock_get_discussion_id_map, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": str(self.course_id)},
            {"body": "foo", "title": "foo", "commentable_id": "wrong_commentable"},
            mock_request
        )

    def test_create_comment(self, mock_request):
        self._setup_mock_request(mock_request)
        with self.assert_discussion_signals('comment_created'):
            response = self.client.post(
                reverse(
                    "create_comment",
                    kwargs={"course_id": str(self.course_id), "thread_id": "dummy"}
                ),
                data={"body": "body"}
            )
        assert response.status_code == 200

    def test_create_comment_no_body(self, mock_request):
        self._test_request_error(
            "create_comment",
            {"thread_id": "dummy", "course_id": str(self.course_id)},
            {},
            mock_request
        )

    def test_create_comment_empty_body(self, mock_request):
        self._test_request_error(
            "create_comment",
            {"thread_id": "dummy", "course_id": str(self.course_id)},
            {"body": " "},
            mock_request
        )

    def test_create_sub_comment_no_body(self, mock_request):
        self._test_request_error(
            "create_sub_comment",
            {"comment_id": "dummy", "course_id": str(self.course_id)},
            {},
            mock_request
        )

    def test_create_sub_comment_empty_body(self, mock_request):
        self._test_request_error(
            "create_sub_comment",
            {"comment_id": "dummy", "course_id": str(self.course_id)},
            {"body": " "},
            mock_request
        )

    def test_update_comment_no_body(self, mock_request):
        self._test_request_error(
            "update_comment",
            {"comment_id": "dummy", "course_id": str(self.course_id)},
            {},
            mock_request
        )

    def test_update_comment_empty_body(self, mock_request):
        self._test_request_error(
            "update_comment",
            {"comment_id": "dummy", "course_id": str(self.course_id)},
            {"body": " "},
            mock_request
        )

    def test_update_comment_basic(self, mock_request):
        self._setup_mock_request(mock_request)
        comment_id = "test_comment_id"
        updated_body = "updated body"
        with self.assert_discussion_signals('comment_edited'):
            response = self.client.post(
                reverse(
                    "update_comment",
                    kwargs={"course_id": str(self.course_id), "comment_id": comment_id}
                ),
                data={"body": updated_body}
            )
        assert response.status_code == 200
        mock_request.assert_called_with(
            "put",
            f"{CS_PREFIX}/comments/{comment_id}",
            headers=ANY,
            params=ANY,
            timeout=ANY,
            data={"body": updated_body}
        )

    def test_flag_thread_open(self, mock_request):
        self.flag_thread(mock_request, False)

    def test_flag_thread_close(self, mock_request):
        self.flag_thread(mock_request, True)

    def flag_thread(self, mock_request, is_closed):
        self._set_mock_request_data(mock_request, {
            "title": "Hello",
            "body": "this is a post",
            "course_id": "MITx/999/Robot_Super_Course",
            "anonymous": False,
            "anonymous_to_peers": False,
            "commentable_id": "i4x-MITx-999-course-Robot_Super_Course",
            "created_at": "2013-05-10T18:53:43Z",
            "updated_at": "2013-05-10T18:53:43Z",
            "at_position_list": [],
            "closed": is_closed,
            "id": "518d4237b023791dca00000d",
            "user_id": "1", "username": "robot",
            "votes": {
                "count": 0,
                "up_count": 0,
                "down_count": 0,
                "point": 0
            },
            "abuse_flaggers": [1],
            "type": "thread",
            "group_id": None,
            "pinned": False,
            "endorsed": False,
            "unread_comments_count": 0,
            "read": False,
            "comments_count": 0,
        })
        url = reverse('flag_abuse_for_thread', kwargs={
            'thread_id': '518d4237b023791dca00000d',
            'course_id': str(self.course_id)
        })
        response = self.client.post(url)
        assert mock_request.called

        call_list = [
            (
                ('get', f'{CS_PREFIX}/threads/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY, 'with_responses': False},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('put', f'{CS_PREFIX}/threads/518d4237b023791dca00000d/abuse_flag'),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('get', f'{CS_PREFIX}/threads/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY, 'with_responses': False},
                    'headers': ANY,
                    'timeout': 5
                }
            )
        ]

        assert mock_request.call_args_list == call_list

        assert response.status_code == 200

    def test_un_flag_thread_open(self, mock_request):
        self.un_flag_thread(mock_request, False)

    def test_un_flag_thread_close(self, mock_request):
        self.un_flag_thread(mock_request, True)

    def un_flag_thread(self, mock_request, is_closed):
        self._set_mock_request_data(mock_request, {
            "title": "Hello",
            "body": "this is a post",
            "course_id": "MITx/999/Robot_Super_Course",
            "anonymous": False,
            "anonymous_to_peers": False,
            "commentable_id": "i4x-MITx-999-course-Robot_Super_Course",
            "created_at": "2013-05-10T18:53:43Z",
            "updated_at": "2013-05-10T18:53:43Z",
            "at_position_list": [],
            "closed": is_closed,
            "id": "518d4237b023791dca00000d",
            "user_id": "1",
            "username": "robot",
            "votes": {
                "count": 0,
                "up_count": 0,
                "down_count": 0,
                "point": 0
            },
            "abuse_flaggers": [],
            "type": "thread",
            "group_id": None,
            "pinned": False,
            "endorsed": False,
            "unread_comments_count": 0,
            "read": False,
            "comments_count": 0
        })
        url = reverse('un_flag_abuse_for_thread', kwargs={
            'thread_id': '518d4237b023791dca00000d',
            'course_id': str(self.course_id)
        })
        response = self.client.post(url)
        assert mock_request.called

        call_list = [
            (
                ('get', f'{CS_PREFIX}/threads/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY, 'with_responses': False},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('put', f'{CS_PREFIX}/threads/518d4237b023791dca00000d/abuse_unflag'),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('get', f'{CS_PREFIX}/threads/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY, 'with_responses': False},
                    'headers': ANY,
                    'timeout': 5
                }
            )
        ]

        assert mock_request.call_args_list == call_list

        assert response.status_code == 200

    def test_flag_comment_open(self, mock_request):
        self.flag_comment(mock_request, False)

    def test_flag_comment_close(self, mock_request):
        self.flag_comment(mock_request, True)

    def flag_comment(self, mock_request, is_closed):
        self._set_mock_request_data(mock_request, {
            "body": "this is a comment",
            "course_id": "MITx/999/Robot_Super_Course",
            "anonymous": False,
            "anonymous_to_peers": False,
            "commentable_id": "i4x-MITx-999-course-Robot_Super_Course",
            "created_at": "2013-05-10T18:53:43Z",
            "updated_at": "2013-05-10T18:53:43Z",
            "at_position_list": [],
            "closed": is_closed,
            "id": "518d4237b023791dca00000d",
            "user_id": "1",
            "username": "robot",
            "votes": {
                "count": 0,
                "up_count": 0,
                "down_count": 0,
                "point": 0
            },
            "abuse_flaggers": [1],
            "type": "comment",
            "endorsed": False
        })
        url = reverse('flag_abuse_for_comment', kwargs={
            'comment_id': '518d4237b023791dca00000d',
            'course_id': str(self.course_id)
        })
        response = self.client.post(url)
        assert mock_request.called

        call_list = [
            (
                ('get', f'{CS_PREFIX}/comments/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('put', f'{CS_PREFIX}/comments/518d4237b023791dca00000d/abuse_flag'),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('get', f'{CS_PREFIX}/comments/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            )
        ]

        assert mock_request.call_args_list == call_list

        assert response.status_code == 200

    def test_un_flag_comment_open(self, mock_request):
        self.un_flag_comment(mock_request, False)

    def test_un_flag_comment_close(self, mock_request):
        self.un_flag_comment(mock_request, True)

    def un_flag_comment(self, mock_request, is_closed):
        self._set_mock_request_data(mock_request, {
            "body": "this is a comment",
            "course_id": "MITx/999/Robot_Super_Course",
            "anonymous": False,
            "anonymous_to_peers": False,
            "commentable_id": "i4x-MITx-999-course-Robot_Super_Course",
            "created_at": "2013-05-10T18:53:43Z",
            "updated_at": "2013-05-10T18:53:43Z",
            "at_position_list": [],
            "closed": is_closed,
            "id": "518d4237b023791dca00000d",
            "user_id": "1",
            "username": "robot",
            "votes": {
                "count": 0,
                "up_count": 0,
                "down_count": 0,
                "point": 0
            },
            "abuse_flaggers": [],
            "type": "comment",
            "endorsed": False
        })
        url = reverse('un_flag_abuse_for_comment', kwargs={
            'comment_id': '518d4237b023791dca00000d',
            'course_id': str(self.course_id)
        })
        response = self.client.post(url)
        assert mock_request.called

        call_list = [
            (
                ('get', f'{CS_PREFIX}/comments/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('put', f'{CS_PREFIX}/comments/518d4237b023791dca00000d/abuse_unflag'),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('get', f'{CS_PREFIX}/comments/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            )
        ]

        assert mock_request.call_args_list == call_list

        assert response.status_code == 200

    @ddt.data(
        ('upvote_thread', 'thread_id', 'thread_voted'),
        ('upvote_comment', 'comment_id', 'comment_voted'),
        ('downvote_thread', 'thread_id', 'thread_voted'),
        ('downvote_comment', 'comment_id', 'comment_voted')
    )
    @ddt.unpack
    def test_voting(self, view_name, item_id, signal, mock_request):
        self._setup_mock_request(mock_request)
        with self.assert_discussion_signals(signal):
            response = self.client.post(
                reverse(
                    view_name,
                    kwargs={item_id: 'dummy', 'course_id': str(self.course_id)}
                )
            )
        assert response.status_code == 200

    def test_endorse_comment(self, mock_request):
        self._setup_mock_request(mock_request)
        self.client.login(username=self.moderator.username, password=self.password)
        with self.assert_discussion_signals('comment_endorsed', user=self.moderator):
            response = self.client.post(
                reverse(
                    'endorse_comment',
                    kwargs={'comment_id': 'dummy', 'course_id': str(self.course_id)}
                )
            )
        assert response.status_code == 200


@patch("openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request", autospec=True)
@disable_signal(views, 'comment_endorsed')
class ViewPermissionsTestCase(ForumsEnableMixin, UrlResetMixin, SharedModuleStoreTestCase, MockRequestSetupMixin):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        seed_permissions_roles(cls.course.id)

        cls.password = "test password"
        cls.student = UserFactory.create(password=cls.password)
        cls.moderator = UserFactory.create(password=cls.password)

        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)
        CourseEnrollmentFactory(user=cls.moderator, course_id=cls.course.id)

        cls.moderator.roles.add(Role.objects.get(name="Moderator", course_id=cls.course.id))

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()

    def test_pin_thread_as_student(self, mock_request):
        self._set_mock_request_data(mock_request, {})
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse("pin_thread", kwargs={"course_id": str(self.course.id), "thread_id": "dummy"})
        )
        assert response.status_code == 401

    def test_pin_thread_as_moderator(self, mock_request):
        self._set_mock_request_data(mock_request, {})
        self.client.login(username=self.moderator.username, password=self.password)
        response = self.client.post(
            reverse("pin_thread", kwargs={"course_id": str(self.course.id), "thread_id": "dummy"})
        )
        assert response.status_code == 200

    def test_un_pin_thread_as_student(self, mock_request):
        self._set_mock_request_data(mock_request, {})
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse("un_pin_thread", kwargs={"course_id": str(self.course.id), "thread_id": "dummy"})
        )
        assert response.status_code == 401

    def test_un_pin_thread_as_moderator(self, mock_request):
        self._set_mock_request_data(mock_request, {})
        self.client.login(username=self.moderator.username, password=self.password)
        response = self.client.post(
            reverse("un_pin_thread", kwargs={"course_id": str(self.course.id), "thread_id": "dummy"})
        )
        assert response.status_code == 200

    def _set_mock_request_thread_and_comment(self, mock_request, thread_data, comment_data):
        def handle_request(*args, **kwargs):
            url = args[1]
            if "/threads/" in url:
                return self._create_response_mock(thread_data)
            elif "/comments/" in url:
                return self._create_response_mock(comment_data)
            else:
                raise ArgumentError("Bad url to mock request")
        mock_request.side_effect = handle_request

    def test_endorse_response_as_staff(self, mock_request):
        self._set_mock_request_thread_and_comment(
            mock_request,
            {"type": "thread", "thread_type": "question", "user_id": str(self.student.id)},
            {"type": "comment", "thread_id": "dummy"}
        )
        self.client.login(username=self.moderator.username, password=self.password)
        response = self.client.post(
            reverse("endorse_comment", kwargs={"course_id": str(self.course.id), "comment_id": "dummy"})
        )
        assert response.status_code == 200

    def test_endorse_response_as_student(self, mock_request):
        self._set_mock_request_thread_and_comment(
            mock_request,
            {"type": "thread", "thread_type": "question", "user_id": str(self.moderator.id)},
            {"type": "comment", "thread_id": "dummy"}
        )
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse("endorse_comment", kwargs={"course_id": str(self.course.id), "comment_id": "dummy"})
        )
        assert response.status_code == 401

    def test_endorse_response_as_student_question_author(self, mock_request):
        self._set_mock_request_thread_and_comment(
            mock_request,
            {"type": "thread", "thread_type": "question", "user_id": str(self.student.id)},
            {"type": "comment", "thread_id": "dummy"}
        )
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse("endorse_comment", kwargs={"course_id": str(self.course.id), "comment_id": "dummy"})
        )
        assert response.status_code == 200


class CreateThreadUnicodeTestCase(
        ForumsEnableMixin,
        SharedModuleStoreTestCase,
        UnicodeTestMixin,
        MockRequestSetupMixin):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        seed_permissions_roles(cls.course.id)
        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)

    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request,):
        """
        Test to make sure unicode data in a thread doesn't break it.
        """
        self._set_mock_request_data(mock_request, {})
        request = RequestFactory().post("dummy_url", {"thread_type": "discussion", "body": text, "title": text})
        request.user = self.student
        request.view_name = "create_thread"
        response = views.create_thread(
            # The commentable ID contains a username, the Unicode char below ensures it works fine
            request, course_id=str(self.course.id), commentable_id="non_tåem_dummy_id"
        )

        assert response.status_code == 200
        assert mock_request.called
        assert mock_request.call_args[1]['data']['body'] == text
        assert mock_request.call_args[1]['data']['title'] == text


@disable_signal(views, 'thread_edited')
class UpdateThreadUnicodeTestCase(
        ForumsEnableMixin,
        SharedModuleStoreTestCase,
        UnicodeTestMixin,
        MockRequestSetupMixin
):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        seed_permissions_roles(cls.course.id)
        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)

    @patch(
        'lms.djangoapps.discussion.django_comment_client.utils.get_discussion_categories_ids',
        return_value=["test_commentable"],
    )
    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request, mock_get_discussion_id_map):
        self._set_mock_request_data(mock_request, {
            "user_id": str(self.student.id),
            "closed": False,
        })
        request = RequestFactory().post("dummy_url", {"body": text, "title": text, "thread_type": "question", "commentable_id": "test_commentable"})
        request.user = self.student
        request.view_name = "update_thread"
        response = views.update_thread(request, course_id=str(self.course.id), thread_id="dummy_thread_id")

        assert response.status_code == 200
        assert mock_request.called
        assert mock_request.call_args[1]['data']['body'] == text
        assert mock_request.call_args[1]['data']['title'] == text
        assert mock_request.call_args[1]['data']['thread_type'] == 'question'
        assert mock_request.call_args[1]['data']['commentable_id'] == 'test_commentable'


@disable_signal(views, 'comment_created')
class CreateCommentUnicodeTestCase(
        ForumsEnableMixin,
        SharedModuleStoreTestCase,
        UnicodeTestMixin,
        MockRequestSetupMixin
):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        seed_permissions_roles(cls.course.id)
        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)

    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):
        commentable_id = "non_team_dummy_id"
        self._set_mock_request_data(mock_request, {
            "closed": False,
            "commentable_id": commentable_id
        })
        # We have to get clever here due to Thread's setters and getters.
        # Patch won't work with it.
        try:
            Thread.commentable_id = commentable_id
            request = RequestFactory().post("dummy_url", {"body": text})
            request.user = self.student
            request.view_name = "create_comment"
            response = views.create_comment(
                request, course_id=str(self.course.id), thread_id="dummy_thread_id"
            )

            assert response.status_code == 200
            assert mock_request.called
            assert mock_request.call_args[1]['data']['body'] == text
        finally:
            del Thread.commentable_id


@disable_signal(views, 'comment_edited')
class UpdateCommentUnicodeTestCase(
        ForumsEnableMixin,
        SharedModuleStoreTestCase,
        UnicodeTestMixin,
        MockRequestSetupMixin
):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        seed_permissions_roles(cls.course.id)
        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)

    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):
        self._set_mock_request_data(mock_request, {
            "user_id": str(self.student.id),
            "closed": False,
        })
        request = RequestFactory().post("dummy_url", {"body": text})
        request.user = self.student
        request.view_name = "update_comment"
        response = views.update_comment(request, course_id=str(self.course.id), comment_id="dummy_comment_id")

        assert response.status_code == 200
        assert mock_request.called
        assert mock_request.call_args[1]['data']['body'] == text


@disable_signal(views, 'comment_created')
class CreateSubCommentUnicodeTestCase(
        ForumsEnableMixin,
        SharedModuleStoreTestCase,
        UnicodeTestMixin,
        MockRequestSetupMixin
):
    """
    Make sure comments under a response can handle unicode.
    """
    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        seed_permissions_roles(cls.course.id)
        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)

    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):
        """
        Create a comment with unicode in it.
        """
        self._set_mock_request_data(mock_request, {
            "closed": False,
            "depth": 1,
            "thread_id": "test_thread",
            "commentable_id": "non_team_dummy_id"
        })
        request = RequestFactory().post("dummy_url", {"body": text})
        request.user = self.student
        request.view_name = "create_sub_comment"
        Thread.commentable_id = "test_commentable"
        try:
            response = views.create_sub_comment(
                request, course_id=str(self.course.id), comment_id="dummy_comment_id"
            )

            assert response.status_code == 200
            assert mock_request.called
            assert mock_request.call_args[1]['data']['body'] == text
        finally:
            del Thread.commentable_id


@ddt.ddt
@patch("openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request", autospec=True)
@disable_signal(views, 'thread_voted')
@disable_signal(views, 'thread_edited')
@disable_signal(views, 'comment_created')
@disable_signal(views, 'comment_voted')
@disable_signal(views, 'comment_deleted')
class TeamsPermissionsTestCase(ForumsEnableMixin, UrlResetMixin, SharedModuleStoreTestCase, MockRequestSetupMixin):
    # Most of the test points use the same ddt data.
    # args: user, commentable_id, status_code
    ddt_permissions_args = [
        # Student in team can do operations on threads/comments within the team commentable.
        ('student_in_team', 'team_commentable_id', 200),
        # Non-team commentables can be edited by any student.
        ('student_in_team', 'course_commentable_id', 200),
        # Student not in team cannot do operations within the team commentable.
        ('student_not_in_team', 'team_commentable_id', 401),
        # Non-team commentables can be edited by any student.
        ('student_not_in_team', 'course_commentable_id', 200),
        # Moderators can always operator on threads within a team, regardless of team membership.
        ('moderator', 'team_commentable_id', 200),
        # Group moderators have regular student privileges for creating a thread and commenting
        ('group_moderator', 'course_commentable_id', 200)
    ]

    def change_divided_discussion_settings(self, scheme):
        """
        Change divided discussion settings for the current course.
        If dividing by cohorts, create and assign users to a cohort.
        """
        enable_cohorts = True if scheme is CourseDiscussionSettings.COHORT else False
        discussion_settings = CourseDiscussionSettings.get(self.course.id)
        discussion_settings.update({
            'enable_cohorts': enable_cohorts,
            'divided_discussions': [],
            'always_divide_inline_discussions': True,
            'division_scheme': scheme,
        })
        set_course_cohorted(self.course.id, enable_cohorts)

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            teams_config_data = {
                'topics': [{'id': "topic_id", 'name': 'Solar Power', 'description': 'Solar power is hot'}]
            }
            cls.course = CourseFactory.create(teams_configuration=TeamsConfig(teams_config_data))

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.course = CourseFactory.create()
        cls.password = "test password"
        seed_permissions_roles(cls.course.id)

        # Create enrollment tracks
        CourseModeFactory.create(
            course_id=cls.course.id,
            mode_slug=CourseMode.VERIFIED
        )
        CourseModeFactory.create(
            course_id=cls.course.id,
            mode_slug=CourseMode.AUDIT
        )

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
                course_id=cls.course.id,
                user=student,
                mode=coursemode
            )
            return student

        cls.student_in_team, cls.student_not_in_team, cls.moderator, cls.cohorted = (
            [create_users_and_enroll(CourseMode.AUDIT) for _ in range(4)])
        cls.verified, cls.group_moderator = [create_users_and_enroll(CourseMode.VERIFIED) for _ in range(2)]

        # Give moderator and group moderator permissions
        cls.moderator.roles.add(Role.objects.get(name="Moderator", course_id=cls.course.id))
        assign_role(cls.course.id, cls.group_moderator, 'Group Moderator')

        # Create a team
        cls.team_commentable_id = "team_discussion_id"
        cls.team = CourseTeamFactory.create(
            name='The Only Team',
            course_id=cls.course.id,
            topic_id='topic_id',
            discussion_topic_id=cls.team_commentable_id
        )
        CourseTeamMembershipFactory.create(team=cls.team, user=cls.student_in_team)

        # Dummy commentable ID not linked to a team
        cls.course_commentable_id = "course_level_commentable"

        # Create cohort and add students to it
        CohortFactory(
            course_id=cls.course.id,
            name='Test Cohort',
            users=[cls.group_moderator, cls.cohorted]
        )

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()

    def _setup_mock(self, user, mock_request, data):
        user = getattr(self, user)
        self._set_mock_request_data(mock_request, data)
        self.client.login(username=user.username, password=self.password)

    @ddt.data(
        # student_in_team will be able to update their own post, regardless of team membership
        ('student_in_team', 'student_in_team', 'team_commentable_id', 200, CourseDiscussionSettings.NONE),
        ('student_in_team', 'student_in_team', 'course_commentable_id', 200, CourseDiscussionSettings.NONE),
        # students can only update their own posts
        ('student_in_team', 'moderator', 'team_commentable_id', 401, CourseDiscussionSettings.NONE),
        # Even though student_not_in_team is not in the team, he can still modify posts he created while in the team.
        ('student_not_in_team', 'student_not_in_team', 'team_commentable_id', 200, CourseDiscussionSettings.NONE),
        # Moderators can change their own posts and other people's posts.
        ('moderator', 'moderator', 'team_commentable_id', 200, CourseDiscussionSettings.NONE),
        ('moderator', 'student_in_team', 'team_commentable_id', 200, CourseDiscussionSettings.NONE),
        # Group moderator can do operations on commentables within their group if the course is divided
        ('group_moderator', 'verified', 'course_commentable_id', 200, CourseDiscussionSettings.ENROLLMENT_TRACK),
        ('group_moderator', 'cohorted', 'course_commentable_id', 200, CourseDiscussionSettings.COHORT),
        # Group moderators cannot do operations on commentables outside of their group
        ('group_moderator', 'verified', 'course_commentable_id', 401, CourseDiscussionSettings.COHORT),
        ('group_moderator', 'cohorted', 'course_commentable_id', 401, CourseDiscussionSettings.ENROLLMENT_TRACK),
        # Group moderators cannot do operations when the course is not divided
        ('group_moderator', 'verified', 'course_commentable_id', 401, CourseDiscussionSettings.NONE),
        ('group_moderator', 'cohorted', 'course_commentable_id', 401, CourseDiscussionSettings.NONE)
    )
    @ddt.unpack
    def test_update_thread(self, user, thread_author, commentable_id, status_code, division_scheme, mock_request):
        """
        Verify that update_thread is limited to thread authors and privileged users (team membership does not matter).
        """
        self.change_divided_discussion_settings(division_scheme)
        commentable_id = getattr(self, commentable_id)
        # thread_author is who is marked as the author of the thread being updated.
        thread_author = getattr(self, thread_author)

        self._setup_mock(
            user, mock_request,  # user is the person making the request.
            {
                "user_id": str(thread_author.id),
                "closed": False, "commentable_id": commentable_id,
                "context": "standalone",
                "username": thread_author.username,
                "course_id": str(self.course.id)
            }
        )
        response = self.client.post(
            reverse(
                "update_thread",
                kwargs={
                    "course_id": str(self.course.id),
                    "thread_id": "dummy"
                }
            ),
            data={"body": "foo", "title": "foo", "commentable_id": commentable_id}
        )
        assert response.status_code == status_code

    @ddt.data(
        # Students can delete their own posts
        ('student_in_team', 'student_in_team', 'team_commentable_id', 200, CourseDiscussionSettings.NONE),
        # Moderators can delete any post
        ('moderator', 'student_in_team', 'team_commentable_id', 200, CourseDiscussionSettings.NONE),
        # Others cannot delete posts
        ('student_in_team', 'moderator', 'team_commentable_id', 401, CourseDiscussionSettings.NONE),
        ('student_not_in_team', 'student_in_team', 'team_commentable_id', 401, CourseDiscussionSettings.NONE),
        # Group moderator can do operations on commentables within their group if the course is divided
        ('group_moderator', 'verified', 'team_commentable_id', 200, CourseDiscussionSettings.ENROLLMENT_TRACK),
        ('group_moderator', 'cohorted', 'team_commentable_id', 200, CourseDiscussionSettings.COHORT),
        # Group moderators cannot do operations on commentables outside of their group
        ('group_moderator', 'verified', 'team_commentable_id', 401, CourseDiscussionSettings.COHORT),
        ('group_moderator', 'cohorted', 'team_commentable_id', 401, CourseDiscussionSettings.ENROLLMENT_TRACK),
        # Group moderators cannot do operations when the course is not divided
        ('group_moderator', 'verified', 'team_commentable_id', 401, CourseDiscussionSettings.NONE),
        ('group_moderator', 'cohorted', 'team_commentable_id', 401, CourseDiscussionSettings.NONE)
    )
    @ddt.unpack
    def test_delete_comment(self, user, comment_author, commentable_id, status_code, division_scheme, mock_request):
        commentable_id = getattr(self, commentable_id)
        comment_author = getattr(self, comment_author)
        self.change_divided_discussion_settings(division_scheme)

        self._setup_mock(user, mock_request, {
            "closed": False,
            "commentable_id": commentable_id,
            "user_id": str(comment_author.id),
            "username": comment_author.username,
            "course_id": str(self.course.id),
            "body": "test body",
        })

        response = self.client.post(
            reverse(
                "delete_comment",
                kwargs={
                    "course_id": str(self.course.id),
                    "comment_id": "dummy"
                }
            ),
            data={"body": "foo", "title": "foo"}
        )
        assert response.status_code == status_code

    @ddt.data(*ddt_permissions_args)
    @ddt.unpack
    def test_create_comment(self, user, commentable_id, status_code, mock_request):
        """
        Verify that create_comment is limited to members of the team or users with 'edit_content' permission.
        """
        commentable_id = getattr(self, commentable_id)
        self._setup_mock(user, mock_request, {"closed": False, "commentable_id": commentable_id})

        response = self.client.post(
            reverse(
                "create_comment",
                kwargs={
                    "course_id": str(self.course.id),
                    "thread_id": "dummy"
                }
            ),
            data={"body": "foo", "title": "foo"}
        )
        assert response.status_code == status_code

    @ddt.data(*ddt_permissions_args)
    @ddt.unpack
    def test_create_sub_comment(self, user, commentable_id, status_code, mock_request):
        """
        Verify that create_subcomment is limited to members of the team or users with 'edit_content' permission.
        """
        commentable_id = getattr(self, commentable_id)
        self._setup_mock(
            user, mock_request,
            {"closed": False, "commentable_id": commentable_id, "thread_id": "dummy_thread"},
        )
        response = self.client.post(
            reverse(
                "create_sub_comment",
                kwargs={
                    "course_id": str(self.course.id),
                    "comment_id": "dummy_comment"
                }
            ),
            data={"body": "foo", "title": "foo"}
        )
        assert response.status_code == status_code

    @ddt.data(*ddt_permissions_args)
    @ddt.unpack
    def test_comment_actions(self, user, commentable_id, status_code, mock_request):
        """
        Verify that voting and flagging of comments is limited to members of the team or users with
        'edit_content' permission.
        """
        commentable_id = getattr(self, commentable_id)
        self._setup_mock(
            user, mock_request,
            {"closed": False, "commentable_id": commentable_id, "thread_id": "dummy_thread", "body": 'dummy body'},
        )
        for action in ["upvote_comment", "downvote_comment", "un_flag_abuse_for_comment", "flag_abuse_for_comment"]:
            response = self.client.post(
                reverse(
                    action,
                    kwargs={"course_id": str(self.course.id), "comment_id": "dummy_comment"}
                )
            )
            assert response.status_code == status_code

    @ddt.data(*ddt_permissions_args)
    @ddt.unpack
    def test_threads_actions(self, user, commentable_id, status_code, mock_request):
        """
        Verify that voting, flagging, and following of threads is limited to members of the team or users with
        'edit_content' permission.
        """
        commentable_id = getattr(self, commentable_id)
        self._setup_mock(
            user, mock_request,
            {"closed": False, "commentable_id": commentable_id, "body": "dummy body"},
        )
        for action in ["upvote_thread", "downvote_thread", "un_flag_abuse_for_thread", "flag_abuse_for_thread",
                       "follow_thread", "unfollow_thread"]:
            response = self.client.post(
                reverse(
                    action,
                    kwargs={"course_id": str(self.course.id), "thread_id": "dummy_thread"}
                )
            )
            assert response.status_code == status_code


TEAM_COMMENTABLE_ID = 'test-team-discussion'


@disable_signal(views, 'comment_created')
@ddt.ddt
class ForumEventTestCase(ForumsEnableMixin, SharedModuleStoreTestCase, MockRequestSetupMixin):
    """
    Forum actions are expected to launch analytics events. Test these here.
    """
    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        seed_permissions_roles(cls.course.id)

        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)
        cls.student.roles.add(Role.objects.get(name="Student", course_id=cls.course.id))
        CourseAccessRoleFactory(course_id=cls.course.id, user=cls.student, role='Wizard')

    @patch('eventtracking.tracker.emit')
    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def test_response_event(self, mock_request, mock_emit):
        """
        Check to make sure an event is fired when a user responds to a thread.
        """
        self._set_mock_request_data(mock_request, {
            "closed": False,
            "commentable_id": 'test_commentable_id',
            'thread_id': 'test_thread_id',
        })
        request = RequestFactory().post("dummy_url", {"body": "Test comment", 'auto_subscribe': True})
        request.user = self.student
        request.view_name = "create_comment"
        views.create_comment(request, course_id=str(self.course.id), thread_id='test_thread_id')

        event_name, event = mock_emit.call_args[0]
        assert event_name == 'edx.forum.response.created'
        assert event['body'] == 'Test comment'
        assert event['commentable_id'] == 'test_commentable_id'
        assert event['user_forums_roles'] == ['Student']
        assert event['user_course_roles'] == ['Wizard']
        assert event['discussion']['id'] == 'test_thread_id'
        assert event['options']['followed'] is True

    @patch('eventtracking.tracker.emit')
    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def test_comment_event(self, mock_request, mock_emit):
        """
        Ensure an event is fired when someone comments on a response.
        """
        self._set_mock_request_data(mock_request, {
            "closed": False,
            "depth": 1,
            "thread_id": "test_thread_id",
            "commentable_id": "test_commentable_id",
            "parent_id": "test_response_id"
        })
        request = RequestFactory().post("dummy_url", {"body": "Another comment"})
        request.user = self.student
        request.view_name = "create_sub_comment"
        views.create_sub_comment(request, course_id=str(self.course.id), comment_id="dummy_comment_id")

        event_name, event = mock_emit.call_args[0]
        assert event_name == 'edx.forum.comment.created'
        assert event['body'] == 'Another comment'
        assert event['discussion']['id'] == 'test_thread_id'
        assert event['response']['id'] == 'test_response_id'
        assert event['user_forums_roles'] == ['Student']
        assert event['user_course_roles'] == ['Wizard']
        assert event['options']['followed'] is False

    @patch('eventtracking.tracker.emit')
    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    @ddt.data((
        'create_thread',
        'edx.forum.thread.created', {
            'thread_type': 'discussion',
            'body': 'Test text',
            'title': 'Test',
            'auto_subscribe': True
        },
        {'commentable_id': TEAM_COMMENTABLE_ID}
    ), (
        'create_comment',
        'edx.forum.response.created',
        {'body': 'Test comment', 'auto_subscribe': True},
        {'thread_id': 'test_thread_id'}
    ), (
        'create_sub_comment',
        'edx.forum.comment.created',
        {'body': 'Another comment'},
        {'comment_id': 'dummy_comment_id'}
    ))
    @ddt.unpack
    def test_team_events(self, view_name, event_name, view_data, view_kwargs, mock_request, mock_emit):
        user = self.student
        team = CourseTeamFactory.create(discussion_topic_id=TEAM_COMMENTABLE_ID)
        CourseTeamMembershipFactory.create(team=team, user=user)

        self._set_mock_request_data(mock_request, {
            'closed': False,
            'commentable_id': TEAM_COMMENTABLE_ID,
            'thread_id': 'test_thread_id',
        })

        request = RequestFactory().post('dummy_url', view_data)
        request.user = user
        request.view_name = view_name

        getattr(views, view_name)(request, course_id=str(self.course.id), **view_kwargs)

        name, event = mock_emit.call_args[0]
        assert name == event_name
        assert event['team_id'] == team.team_id

    @ddt.data(
        ('vote_for_thread', 'thread_id', 'thread'),
        ('undo_vote_for_thread', 'thread_id', 'thread'),
        ('vote_for_comment', 'comment_id', 'response'),
        ('undo_vote_for_comment', 'comment_id', 'response'),
    )
    @ddt.unpack
    @patch('eventtracking.tracker.emit')
    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def test_thread_voted_event(self, view_name, obj_id_name, obj_type, mock_request, mock_emit):
        undo = view_name.startswith('undo')

        self._set_mock_request_data(mock_request, {
            'closed': False,
            'commentable_id': 'test_commentable_id',
            'username': 'gumprecht',
        })
        request = RequestFactory().post('dummy_url', {})
        request.user = self.student
        request.view_name = view_name
        view_function = getattr(views, view_name)
        kwargs = dict(course_id=str(self.course.id))
        kwargs[obj_id_name] = obj_id_name
        if not undo:
            kwargs.update(value='up')
        view_function(request, **kwargs)

        assert mock_emit.called
        event_name, event = mock_emit.call_args[0]
        assert event_name == f'edx.forum.{obj_type}.voted'
        assert event['target_username'] == 'gumprecht'
        assert event['undo_vote'] == undo
        assert event['vote_value'] == 'up'


class UsersEndpointTestCase(ForumsEnableMixin, SharedModuleStoreTestCase, MockRequestSetupMixin):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        seed_permissions_roles(cls.course.id)

        cls.student = UserFactory.create()
        cls.enrollment = CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)
        cls.other_user = UserFactory.create(username="other")
        CourseEnrollmentFactory(user=cls.other_user, course_id=cls.course.id)

    def set_post_counts(self, mock_request, threads_count=1, comments_count=1):
        """
        sets up a mock response from the comments service for getting post counts for our other_user
        """
        self._set_mock_request_data(mock_request, {
            "threads_count": threads_count,
            "comments_count": comments_count,
        })

    def make_request(self, method='get', course_id=None, **kwargs):
        course_id = course_id or self.course.id
        request = getattr(RequestFactory(), method)("dummy_url", kwargs)
        request.user = self.student
        request.view_name = "users"
        return views.users(request, course_id=str(course_id))

    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def test_finds_exact_match(self, mock_request):
        self.set_post_counts(mock_request)
        response = self.make_request(username="other")
        assert response.status_code == 200
        assert json.loads(response.content.decode('utf-8'))['users'] == [{'id': self.other_user.id, 'username': self.other_user.username}]

    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def test_finds_no_match(self, mock_request):
        self.set_post_counts(mock_request)
        response = self.make_request(username="othor")
        assert response.status_code == 200
        assert json.loads(response.content.decode('utf-8'))['users'] == []

    def test_requires_GET(self):
        response = self.make_request(method='post', username="other")
        assert response.status_code == 405

    def test_requires_username_param(self):
        response = self.make_request()
        assert response.status_code == 400
        content = json.loads(response.content.decode('utf-8'))
        assert 'errors' in content
        assert 'users' not in content

    def test_course_does_not_exist(self):
        course_id = CourseKey.from_string("does/not/exist")
        response = self.make_request(course_id=course_id, username="other")

        assert response.status_code == 404
        content = json.loads(response.content.decode('utf-8'))
        assert 'errors' in content
        assert 'users' not in content

    def test_requires_requestor_enrolled_in_course(self):
        # unenroll self.student from the course.
        self.enrollment.delete()

        response = self.make_request(username="other")
        assert response.status_code == 404
        content = json.loads(response.content.decode('utf-8'))
        assert 'errors' in content
        assert 'users' not in content

    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def test_requires_matched_user_has_forum_content(self, mock_request):
        self.set_post_counts(mock_request, 0, 0)
        response = self.make_request(username="other")
        assert response.status_code == 200
        assert json.loads(response.content.decode('utf-8'))['users'] == []


@ddt.ddt
class SegmentIOForumThreadViewedEventTestCase(SegmentIOTrackingTestCaseBase):

    def _raise_navigation_event(self, label, include_name):
        middleware = TrackMiddleware()
        kwargs = {'label': label}
        if include_name:
            kwargs['name'] = 'edx.bi.app.navigation.screen'
        else:
            kwargs['exclude_name'] = True
        request = self.create_request(
            data=self.create_segmentio_event_json(**kwargs),
            content_type='application/json',
        )
        User.objects.create(pk=SEGMENTIO_TEST_USER_ID, username=str(mock.sentinel.username))
        middleware.process_request(request)
        try:
            response = segmentio.segmentio_event(request)
            assert response.status_code == 200
        finally:
            middleware.process_response(request, None)

    @ddt.data(True, False)
    def test_thread_viewed(self, include_name):
        """
        Tests that a SegmentIO thread viewed event is accepted and transformed.

        Only tests that the transformation happens at all; does not
        comprehensively test that it happens correctly.
        ForumThreadViewedEventTransformerTestCase tests for correctness.
        """
        self._raise_navigation_event('Forum: View Thread', include_name)
        event = self.get_event()
        assert event['name'] == 'edx.forum.thread.viewed'
        assert event['event_type'] == event['name']

    @ddt.data(True, False)
    def test_non_thread_viewed(self, include_name):
        """
        Tests that other BI events are thrown out.
        """
        self._raise_navigation_event('Forum: Create Thread', include_name)
        self.assert_no_events_emitted()


def _get_transformed_event(input_event):
    transformer = ForumThreadViewedEventTransformer(**input_event)
    transformer.transform()
    return transformer


def _create_event(
    label='Forum: View Thread',
    include_context=True,
    inner_context=None,
    username=None,
    course_id=None,
    **event_data
):
    result = {'name': 'edx.bi.app.navigation.screen'}
    if include_context:
        result['context'] = {'label': label}
        if course_id:
            result['context']['course_id'] = str(course_id)
    if username:
        result['username'] = username
    if event_data:
        result['event'] = event_data
    if inner_context:
        if not event_data:
            result['event'] = {}
        result['event']['context'] = inner_context
    return result


def _create_and_transform_event(**kwargs):
    event = _create_event(**kwargs)
    return event, _get_transformed_event(event)


@ddt.ddt
class ForumThreadViewedEventTransformerTestCase(ForumsEnableMixin, UrlResetMixin, ModuleStoreTestCase):
    """
    Test that the ForumThreadViewedEventTransformer transforms events correctly
    and without raising exceptions.

    Because the events passed through the transformer can come from external
    sources (e.g., a mobile app), we carefully test a myriad of cases, including
    those with incomplete and malformed events.
    """
    MODULESTORE = TEST_DATA_MONGO_AMNESTY_MODULESTORE

    CATEGORY_ID = 'i4x-edx-discussion-id'
    CATEGORY_NAME = 'Discussion 1'
    PARENT_CATEGORY_NAME = 'Chapter 1'

    TEAM_CATEGORY_ID = 'i4x-edx-team-discussion-id'
    TEAM_CATEGORY_NAME = 'Team Chat'
    TEAM_PARENT_CATEGORY_NAME = PARENT_CATEGORY_NAME

    DUMMY_CATEGORY_ID = 'i4x-edx-dummy-commentable-id'
    DUMMY_THREAD_ID = 'dummy_thread_id'

    @mock.patch.dict("common.djangoapps.student.models.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        self.courses_by_store = {
            ModuleStoreEnum.Type.mongo: CourseFactory.create(
                org='TestX',
                course='TR-101',
                run='Event_Transform_Test',
                default_store=ModuleStoreEnum.Type.mongo,
            ),
            ModuleStoreEnum.Type.split: CourseFactory.create(
                org='TestX',
                course='TR-101S',
                run='Event_Transform_Test_Split',
                default_store=ModuleStoreEnum.Type.split,
            ),
        }
        self.course = self.courses_by_store['mongo']
        self.student = UserFactory.create()
        self.staff = UserFactory.create(is_staff=True)
        UserBasedRole(user=self.staff, role=CourseStaffRole.ROLE).add_course(self.course.id)
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        self.category = ItemFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id=self.CATEGORY_ID,
            discussion_category=self.PARENT_CATEGORY_NAME,
            discussion_target=self.CATEGORY_NAME,
        )
        self.team_category = ItemFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id=self.TEAM_CATEGORY_ID,
            discussion_category=self.TEAM_PARENT_CATEGORY_NAME,
            discussion_target=self.TEAM_CATEGORY_NAME,
        )
        self.team = CourseTeamFactory.create(
            name='Team 1',
            course_id=self.course.id,
            topic_id='arbitrary-topic-id',
            discussion_topic_id=self.team_category.discussion_id,
        )

    def test_missing_context(self):
        event = _create_event(include_context=False)
        with pytest.raises(EventEmissionExit):
            _get_transformed_event(event)

    def test_no_data(self):
        event, event_trans = _create_and_transform_event()
        event['name'] = 'edx.forum.thread.viewed'
        event['event_type'] = event['name']
        event['event'] = {}
        self.assertDictEqual(event_trans, event)

    def test_inner_context(self):
        _, event_trans = _create_and_transform_event(inner_context={})
        assert 'context' not in event_trans['event']

    def test_non_thread_view(self):
        event = _create_event(
            label='Forum: Create Thread',
            course_id=self.course.id,
            topic_id=self.DUMMY_CATEGORY_ID,
            thread_id=self.DUMMY_THREAD_ID,
        )
        with pytest.raises(EventEmissionExit):
            _get_transformed_event(event)

    def test_bad_field_types(self):
        event, event_trans = _create_and_transform_event(
            course_id={},
            topic_id=3,
            thread_id=object(),
            action=3.14,
        )
        event['name'] = 'edx.forum.thread.viewed'
        event['event_type'] = event['name']
        self.assertDictEqual(event_trans, event)

    def test_bad_course_id(self):
        event, event_trans = _create_and_transform_event(course_id='non-existent-course-id')
        event_data = event_trans['event']
        assert 'category_id' not in event_data
        assert 'category_name' not in event_data
        assert 'url' not in event_data
        assert 'user_forums_roles' not in event_data
        assert 'user_course_roles' not in event_data

    def test_bad_username(self):
        event, event_trans = _create_and_transform_event(username='non-existent-username')
        event_data = event_trans['event']
        assert 'category_id' not in event_data
        assert 'category_name' not in event_data
        assert 'user_forums_roles' not in event_data
        assert 'user_course_roles' not in event_data

    def test_bad_url(self):
        event, event_trans = _create_and_transform_event(
            course_id=self.course.id,
            topic_id='malformed/commentable/id',
            thread_id='malformed/thread/id',
        )
        assert 'url' not in event_trans['event']

    def test_renamed_fields(self):
        AUTHOR = 'joe-the-plumber'
        event, event_trans = _create_and_transform_event(
            course_id=self.course.id,
            topic_id=self.DUMMY_CATEGORY_ID,
            thread_id=self.DUMMY_THREAD_ID,
            author=AUTHOR,
        )
        assert event_trans['event']['commentable_id'] == self.DUMMY_CATEGORY_ID
        assert event_trans['event']['id'] == self.DUMMY_THREAD_ID
        assert event_trans['event']['target_username'] == AUTHOR

    def test_titles(self):

        # No title
        _, event_1_trans = _create_and_transform_event()
        assert 'title' not in event_1_trans['event']
        assert 'title_truncated' not in event_1_trans['event']

        # Short title
        _, event_2_trans = _create_and_transform_event(
            action='!',
        )
        assert 'title' in event_2_trans['event']
        assert 'title_truncated' in event_2_trans['event']
        assert not event_2_trans['event']['title_truncated']

        # Long title
        _, event_3_trans = _create_and_transform_event(
            action=('covfefe' * 200),
        )
        assert 'title' in event_3_trans['event']
        assert 'title_truncated' in event_3_trans['event']
        assert event_3_trans['event']['title_truncated']

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_urls(self, store):
        course = self.courses_by_store[store]
        commentable_id = self.DUMMY_CATEGORY_ID
        thread_id = self.DUMMY_THREAD_ID
        _, event_trans = _create_and_transform_event(
            course_id=course.id,
            topic_id=commentable_id,
            thread_id=thread_id,
        )
        expected_path = '/courses/{}/discussion/forum/{}/threads/{}'.format(
            course.id, commentable_id, thread_id
        )
        assert event_trans['event'].get('url').endswith(expected_path)

    def test_categories(self):

        # Bad category
        _, event_trans_1 = _create_and_transform_event(
            username=self.student.username,
            course_id=self.course.id,
            topic_id='non-existent-category-id',
        )
        assert 'category_id' not in event_trans_1['event']
        assert 'category_name' not in event_trans_1['event']

        # Good category
        _, event_trans_2 = _create_and_transform_event(
            username=self.student.username,
            course_id=self.course.id,
            topic_id=self.category.discussion_id,
        )
        assert event_trans_2['event'].get('category_id') == self.category.discussion_id
        full_category_name = f'{self.category.discussion_category} / {self.category.discussion_target}'
        assert event_trans_2['event'].get('category_name') == full_category_name

    def test_roles(self):

        # No user
        _, event_trans_1 = _create_and_transform_event(
            course_id=self.course.id,
        )
        assert 'user_forums_roles' not in event_trans_1['event']
        assert 'user_course_roles' not in event_trans_1['event']

        # Student user
        _, event_trans_2 = _create_and_transform_event(
            course_id=self.course.id,
            username=self.student.username,
        )
        assert event_trans_2['event'].get('user_forums_roles') == [FORUM_ROLE_STUDENT]
        assert event_trans_2['event'].get('user_course_roles') == []

        # Course staff user
        _, event_trans_3 = _create_and_transform_event(
            course_id=self.course.id,
            username=self.staff.username,
        )
        assert event_trans_3['event'].get('user_forums_roles') == []
        assert event_trans_3['event'].get('user_course_roles') == [CourseStaffRole.ROLE]

    def test_teams(self):

        # No category
        _, event_trans_1 = _create_and_transform_event(
            course_id=self.course.id,
        )
        assert 'team_id' not in event_trans_1

        # Non-team category
        _, event_trans_2 = _create_and_transform_event(
            course_id=self.course.id,
            topic_id=self.CATEGORY_ID,
        )
        assert 'team_id' not in event_trans_2

        # Team category
        _, event_trans_3 = _create_and_transform_event(
            course_id=self.course.id,
            topic_id=self.TEAM_CATEGORY_ID,
        )
        assert event_trans_3['event'].get('team_id') == self.team.team_id

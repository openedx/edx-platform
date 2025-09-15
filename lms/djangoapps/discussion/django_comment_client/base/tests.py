# pylint: skip-file
"""Tests for django comment client views."""

import pytest
import json
import logging
from unittest import mock
from unittest.mock import ANY, Mock, patch

import ddt
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test.client import RequestFactory
from django.urls import reverse
from eventtracking.processors.exceptions import EventEmissionExit
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.roles import CourseStaffRole, UserBasedRole
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from common.djangoapps.track.middleware import TrackMiddleware
from common.djangoapps.track.views import segmentio
from common.djangoapps.track.views.tests.base import SEGMENTIO_TEST_USER_ID, SegmentIOTrackingTestCaseBase
from common.djangoapps.util.testing import UrlResetMixin
from lms.djangoapps.discussion.django_comment_client.base import views
from lms.djangoapps.discussion.django_comment_client.tests.utils import ForumsEnableMixin
from lms.djangoapps.teams.tests.factories import CourseTeamFactory
from openedx.core.djangoapps.django_comment_common.comment_client import Thread
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_STUDENT,
    Role
)
from openedx.core.djangoapps.django_comment_common.utils import (
    ThreadContext,
    seed_permissions_roles,
)
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase, SharedModuleStoreTestCase,
)
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory

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


class ViewsTestCaseMixin:

    def set_up_course(self, block_count=0):
        """
        Creates a course, optionally with block_count discussion blocks, and
        a user with appropriate permissions.
        """

        # create a course
        self.course = CourseFactory.create(
            org='MITx', course='999',
            discussion_topics={"Some Topic": {"id": "some_topic"}},
            display_name='Robot Super Course',
        )
        self.course_id = self.course.id

        # add some discussion blocks
        for i in range(block_count):
            BlockFactory.create(
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
        with patch('common.djangoapps.student.models.user.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            self.password = 'Password1234'

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
            "commentable_id": "non_team_dummy_id",
            "thread_id": "dummy",
            "thread_type": "discussion"
        }
        if include_depth:
            data["depth"] = 0
        self._set_mock_request_data(mock_request, data)

    def create_thread_helper(self, mock_is_forum_v2_enabled, mock_request, extra_request_data=None, extra_response_data=None):
        """
        Issues a request to create a thread and verifies the result.
        """
        mock_is_forum_v2_enabled.return_value = False
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

    def update_thread_helper(self, mock_is_forum_v2_enabled, mock_request):
        """
        Issues a request to update a thread and verifies the result.
        """
        mock_is_forum_v2_enabled.return_value = False
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

    def set_post_counts(self, mock_is_forum_v2_enabled, mock_request, threads_count=1, comments_count=1):
        """
        sets up a mock response from the comments service for getting post counts for our other_user
        """
        mock_is_forum_v2_enabled.return_value = False
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
    @patch('openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled', autospec=True)
    def test_finds_exact_match(self, mock_is_forum_v2_enabled, mock_request):
        self.set_post_counts(mock_is_forum_v2_enabled, mock_request)
        response = self.make_request(username="other")
        assert response.status_code == 200
        assert json.loads(response.content.decode('utf-8'))['users'] == [{'id': self.other_user.id, 'username': self.other_user.username}]

    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    @patch('openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled', autospec=True)
    def test_finds_no_match(self, mock_is_forum_v2_enabled, mock_request):
        self.set_post_counts(mock_is_forum_v2_enabled, mock_request)
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
    @patch('openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled', autospec=True)
    def test_requires_matched_user_has_forum_content(self, mock_is_forum_v2_enabled, mock_request):
        self.set_post_counts(mock_is_forum_v2_enabled, mock_request, 0, 0)
        response = self.make_request(username="other")
        assert response.status_code == 200
        assert json.loads(response.content.decode('utf-8'))['users'] == []


@ddt.ddt
class SegmentIOForumThreadViewedEventTestCase(SegmentIOTrackingTestCaseBase):

    def _raise_navigation_event(self, label, include_name):
        middleware = TrackMiddleware(get_response=lambda request: None)
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
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

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
        self.course = CourseFactory.create(
            org='TestX',
            course='TR-101S',
            run='Event_Transform_Test_Split',
            default_store=ModuleStoreEnum.Type.split,
        )
        self.student = UserFactory.create()
        self.staff = UserFactory.create(is_staff=True)
        UserBasedRole(user=self.staff, role=CourseStaffRole.ROLE).add_course(self.course.id)
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        self.category = BlockFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id=self.CATEGORY_ID,
            discussion_category=self.PARENT_CATEGORY_NAME,
            discussion_target=self.CATEGORY_NAME,
        )
        self.team_category = BlockFactory.create(
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

    def test_urls(self):
        commentable_id = self.DUMMY_CATEGORY_ID
        thread_id = self.DUMMY_THREAD_ID
        _, event_trans = _create_and_transform_event(
            course_id=self.course.id,
            topic_id=commentable_id,
            thread_id=thread_id,
        )
        expected_path = '/courses/{}/discussion/forum/{}/threads/{}'.format(
            self.course.id, commentable_id, thread_id
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

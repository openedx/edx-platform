"""
Tests the forum notification views.
"""
import json
import logging
from datetime import datetime
from unittest import mock
from unittest.mock import ANY, Mock, call, patch

import ddt
import pytest
from django.conf import settings
from django.http import Http404
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import translation
from edx_django_utils.cache import RequestCache
from edx_toggles.toggles.testutils import override_waffle_flag
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_SPLIT_MODULESTORE,
    ModuleStoreTestCase,
    SharedModuleStoreTestCase
)
from xmodule.modulestore.tests.factories import (
    CourseFactory,
    BlockFactory,
)

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.roles import CourseStaffRole, UserBasedRole
from common.djangoapps.student.tests.factories import AdminFactory, CourseEnrollmentFactory, UserFactory
from common.djangoapps.util.testing import EventTestMixin, UrlResetMixin
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from lms.djangoapps.discussion import views
from lms.djangoapps.discussion.django_comment_client.constants import TYPE_ENTRY, TYPE_SUBCATEGORY
from lms.djangoapps.discussion.django_comment_client.permissions import get_team
from lms.djangoapps.discussion.django_comment_client.tests.group_id import (
    CohortedTopicGroupIdTestMixin,
    GroupIdAssertionMixin,
)
from lms.djangoapps.discussion.django_comment_client.tests.unicode import UnicodeTestMixin
from lms.djangoapps.discussion.django_comment_client.tests.utils import (
    CohortedTestCase,
    ForumsEnableMixin,
    config_course_discussions,
    topic_name_to_id
)
from lms.djangoapps.discussion.django_comment_client.utils import strip_none
from lms.djangoapps.discussion.toggles import ENABLE_DISCUSSIONS_MFE
from lms.djangoapps.discussion.views import _get_discussion_default_topic_id, course_discussions_settings_handler
from lms.djangoapps.teams.tests.factories import CourseTeamFactory, CourseTeamMembershipFactory
from openedx.core.djangoapps.course_groups.tests.helpers import config_course_cohorts
from openedx.core.djangoapps.course_groups.tests.test_views import CohortViewsTestCase
from openedx.core.djangoapps.django_comment_common.comment_client.utils import CommentClientPaginatedResult
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_STUDENT,
    CourseDiscussionSettings,
    ForumsConfig
)
from openedx.core.djangoapps.django_comment_common.utils import ThreadContext, seed_permissions_roles
from openedx.core.djangoapps.util.testing import ContentGroupTestCase
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
from openedx.core.lib.teams_config import TeamsConfig

log = logging.getLogger(__name__)

QUERY_COUNT_TABLE_IGNORELIST = WAFFLE_TABLES


class ViewsExceptionTestCase(UrlResetMixin, ModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):

        # Patching the ENABLE_DISCUSSION_SERVICE value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super().setUp()

        # create a course
        self.course = CourseFactory.create(org='MITx', course='999',
                                           display_name='Robot Super Course')

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('common.djangoapps.student.models.user.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            password = 'test'

            # Create the student
            self.student = UserFactory(username=uname, password=password, email=email)

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

            # Log the student in
            self.client = Client()
            assert self.client.login(username=uname, password=password)

        config = ForumsConfig.current()
        config.enabled = True
        config.save()
        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)

    @patch('common.djangoapps.student.models.user.cc.User.from_django_user')
    @patch('openedx.core.djangoapps.django_comment_common.comment_client.user.User.active_threads')
    def test_user_profile_exception(self, mock_threads, mock_from_django_user):

        # Mock the code that makes the HTTP requests to the cs_comment_service app
        # for the profiled user's active threads
        mock_threads.return_value = [], 1, 1

        # Mock the code that makes the HTTP request to the cs_comment_service app
        # that gets the current user's info
        mock_from_django_user.return_value = Mock()

        url = reverse('user_profile',
                      kwargs={'course_id': str(self.course.id), 'user_id': '12345'})  # There is no user 12345
        response = self.client.get(url)
        assert response.status_code == 404

    @patch('common.djangoapps.student.models.user.cc.User.from_django_user')
    @patch('common.djangoapps.student.models.user.cc.User.subscribed_threads')
    def test_user_followed_threads_exception(self, mock_threads, mock_from_django_user):

        # Mock the code that makes the HTTP requests to the cs_comment_service app
        # for the profiled user's active threads
        mock_threads.return_value = CommentClientPaginatedResult(collection=[], page=1, num_pages=1)

        # Mock the code that makes the HTTP request to the cs_comment_service app
        # that gets the current user's info
        mock_from_django_user.return_value = Mock()

        url = reverse('followed_threads',
                      kwargs={'course_id': str(self.course.id), 'user_id': '12345'})  # There is no user 12345
        response = self.client.get(url)
        assert response.status_code == 404


def make_mock_thread_data(  # lint-amnesty, pylint: disable=missing-function-docstring
        course,
        text,
        thread_id,
        num_children,
        group_id=None,
        group_name=None,
        commentable_id=None,
        is_commentable_divided=None,
        anonymous=False,
        anonymous_to_peers=False,
):
    data_commentable_id = (
        commentable_id or course.discussion_topics.get('General', {}).get('id') or "dummy_commentable_id"
    )
    thread_data = {
        "id": thread_id,
        "type": "thread",
        "title": text,
        "body": text,
        "commentable_id": data_commentable_id,
        "resp_total": 42,
        "resp_skip": 25,
        "resp_limit": 5,
        "group_id": group_id,
        "anonymous": anonymous,
        "anonymous_to_peers": anonymous_to_peers,
        "context": (
            ThreadContext.COURSE if get_team(data_commentable_id) is None else ThreadContext.STANDALONE
        )
    }
    if group_id is not None:
        thread_data['group_name'] = group_name
    if is_commentable_divided is not None:
        thread_data['is_commentable_divided'] = is_commentable_divided
    if num_children is not None:
        thread_data["children"] = [{
            "id": f"dummy_comment_id_{i}",
            "type": "comment",
            "body": text,
        } for i in range(num_children)]
    return thread_data


def make_mock_collection_data(  # lint-amnesty, pylint: disable=missing-function-docstring
    course,
    text,
    thread_id,
    num_children=None,
    group_id=None,
    commentable_id=None,
    thread_list=None
):
    if thread_list:
        return [
            make_mock_thread_data(course=course, text=text, num_children=num_children, **thread)
            for thread in thread_list
        ]
    else:
        return [
            make_mock_thread_data(
                course=course,
                text=text,
                thread_id=thread_id,
                num_children=num_children,
                group_id=group_id,
                commentable_id=commentable_id,
            )
        ]


def make_mock_perform_request_impl(  # lint-amnesty, pylint: disable=missing-function-docstring
        course,
        text,
        thread_id="dummy_thread_id",
        group_id=None,
        commentable_id=None,
        num_thread_responses=1,
        thread_list=None,
        anonymous=False,
        anonymous_to_peers=False,
):
    def mock_perform_request_impl(*args, **kwargs):
        url = args[1]
        if url.endswith("threads") or url.endswith("user_profile"):
            return {
                "collection": make_mock_collection_data(
                    course, text, thread_id, None, group_id, commentable_id, thread_list
                )
            }
        elif thread_id and url.endswith(thread_id):
            return make_mock_thread_data(
                course=course,
                text=text,
                thread_id=thread_id,
                num_children=num_thread_responses,
                group_id=group_id,
                commentable_id=commentable_id,
                anonymous=anonymous,
                anonymous_to_peers=anonymous_to_peers,
            )
        elif "/users/" in url:
            res = {
                "default_sort_key": "date",
                "upvoted_ids": [],
                "downvoted_ids": [],
                "subscribed_thread_ids": [],
            }
            # comments service adds these attributes when course_id param is present
            if kwargs.get('params', {}).get('course_id'):
                res.update({
                    "threads_count": 1,
                    "comments_count": 2
                })
            return res
        else:
            return None
    return mock_perform_request_impl


def make_mock_request_impl(  # lint-amnesty, pylint: disable=missing-function-docstring
        course,
        text,
        thread_id="dummy_thread_id",
        group_id=None,
        commentable_id=None,
        num_thread_responses=1,
        thread_list=None,
        anonymous=False,
        anonymous_to_peers=False,
):
    impl = make_mock_perform_request_impl(
        course,
        text,
        thread_id=thread_id,
        group_id=group_id,
        commentable_id=commentable_id,
        num_thread_responses=num_thread_responses,
        thread_list=thread_list,
        anonymous=anonymous,
        anonymous_to_peers=anonymous_to_peers,
    )

    def mock_request_impl(*args, **kwargs):
        data = impl(*args, **kwargs)
        if data:
            return Mock(status_code=200, text=json.dumps(data), json=Mock(return_value=data))
        else:
            return Mock(status_code=404)
    return mock_request_impl


class StringEndsWithMatcher:  # lint-amnesty, pylint: disable=missing-class-docstring
    def __init__(self, suffix):
        self.suffix = suffix

    def __eq__(self, other):
        return other.endswith(self.suffix)


class PartialDictMatcher:  # lint-amnesty, pylint: disable=missing-class-docstring
    def __init__(self, expected_values):
        self.expected_values = expected_values

    def __eq__(self, other):
        return all(
            key in other and other[key] == value
            for key, value in self.expected_values.items()
        )


@patch('requests.request', autospec=True)
class SingleThreadTestCase(ForumsEnableMixin, ModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    CREATE_USER = False

    def setUp(self):
        super().setUp()
        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)

        self.course = CourseFactory.create(discussion_topics={'dummy discussion': {'id': 'dummy_discussion_id'}})
        self.student = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)

    def test_ajax(self, mock_request):
        text = "dummy content"
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text, thread_id=thread_id)

        request = RequestFactory().get(
            "dummy_url",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        request.user = self.student
        response = views.single_thread(
            request,
            str(self.course.id),
            "dummy_discussion_id",
            "test_thread_id"
        )

        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        # strip_none is being used to perform the same transform that the
        # django view performs prior to writing thread data to the response
        assert response_data['content'] == strip_none(make_mock_thread_data(
            course=self.course,
            text=text,
            thread_id=thread_id,
            num_children=1
        ))
        mock_request.assert_called_with(
            "get",
            StringEndsWithMatcher(thread_id),  # url
            data=None,
            params=PartialDictMatcher({"mark_as_read": True, "user_id": 1, "recursive": True}),
            headers=ANY,
            timeout=ANY
        )

    def test_skip_limit(self, mock_request):
        text = "dummy content"
        thread_id = "test_thread_id"
        response_skip = "45"
        response_limit = "15"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text, thread_id=thread_id)

        request = RequestFactory().get(
            "dummy_url",
            {"resp_skip": response_skip, "resp_limit": response_limit},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        request.user = self.student
        response = views.single_thread(
            request,
            str(self.course.id),
            "dummy_discussion_id",
            "test_thread_id"
        )
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        # strip_none is being used to perform the same transform that the
        # django view performs prior to writing thread data to the response
        assert response_data['content'] == strip_none(make_mock_thread_data(
            course=self.course,
            text=text,
            thread_id=thread_id,
            num_children=1
        ))
        mock_request.assert_called_with(
            "get",
            StringEndsWithMatcher(thread_id),  # url
            data=None,
            params=PartialDictMatcher({
                "mark_as_read": True,
                "user_id": 1,
                "recursive": True,
                "resp_skip": response_skip,
                "resp_limit": response_limit,
            }),
            headers=ANY,
            timeout=ANY
        )

    def test_post(self, _mock_request):
        request = RequestFactory().post("dummy_url")
        response = views.single_thread(
            request,
            str(self.course.id),
            "dummy_discussion_id",
            "dummy_thread_id"
        )
        assert response.status_code == 405

    def test_post_anonymous_to_ta(self, mock_request):
        text = "dummy content"
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text, thread_id=thread_id,
                                                          anonymous_to_peers=True)

        request = RequestFactory().get(
            "dummy_url",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        request.user = self.student
        request.user.is_community_ta = True
        response = views.single_thread(
            request,
            str(self.course.id),
            "dummy_discussion_id",
            "test_thread_id"
        )

        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        # user is community ta, so response must not have username and user_id fields
        assert response_data['content'].get('username') is None
        assert response_data['content'].get('user_id') is None

    def test_not_found(self, mock_request):
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        # Mock request to return 404 for thread request
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy", thread_id=None)
        self.assertRaises(
            Http404,
            views.single_thread,
            request,
            str(self.course.id),
            "test_discussion_id",
            "test_thread_id"
        )

    def test_private_team_thread_html(self, mock_request):
        discussion_topic_id = 'dummy_discussion_id'
        thread_id = 'test_thread_id'
        CourseTeamFactory.create(discussion_topic_id=discussion_topic_id)
        user_not_in_team = UserFactory.create()
        CourseEnrollmentFactory.create(user=user_not_in_team, course_id=self.course.id)
        self.client.login(username=user_not_in_team.username, password=self.TEST_PASSWORD)

        mock_request.side_effect = make_mock_request_impl(
            course=self.course,
            text="dummy",
            thread_id=thread_id,
            commentable_id=discussion_topic_id
        )
        with patch('lms.djangoapps.teams.api.is_team_discussion_private', autospec=True) as mocked:
            mocked.return_value = True
            response = self.client.get(
                reverse('single_thread', kwargs={
                    'course_id': str(self.course.id),
                    'discussion_id': discussion_topic_id,
                    'thread_id': thread_id,
                })
            )
            assert response.status_code == 200
            assert response['Content-Type'] == 'text/html; charset=utf-8'
            html = response.content.decode('utf-8')
            # Verify that the access denied error message is in the HTML
            assert 'This is a private discussion. You do not have permissions to view this discussion' in html


class AllowPlusOrMinusOneInt(int):
    """
    A workaround for the fact that assertNumQueries doesn't let you
    specify a range or any tolerance. An 'int' that is 'equal to' its value,
    but also its value +/- 1
    """

    def __init__(self, value):
        super().__init__()
        self.value = value
        self.values = (value, value - 1, value + 1)

    def __eq__(self, other):
        return other in self.values

    def __repr__(self):
        return f"({self.value} +/- 1)"


@patch('requests.request', autospec=True)
class SingleCohortedThreadTestCase(CohortedTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def setUp(self):
        super().setUp()
        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)

    def _create_mock_cohorted_thread(self, mock_request):  # lint-amnesty, pylint: disable=missing-function-docstring
        mock_text = "dummy content"
        mock_thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text=mock_text,
            thread_id=mock_thread_id,
            group_id=self.student_cohort.id,
            commentable_id="cohorted_topic",
        )
        return mock_text, mock_thread_id

    def test_ajax(self, mock_request):
        mock_text, mock_thread_id = self._create_mock_cohorted_thread(mock_request)

        request = RequestFactory().get(
            "dummy_url",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        request.user = self.student
        response = views.single_thread(
            request,
            str(self.course.id),
            "cohorted_topic",
            mock_thread_id
        )

        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data['content'] == make_mock_thread_data(
            course=self.course,
            commentable_id='cohorted_topic',
            text=mock_text,
            thread_id=mock_thread_id,
            num_children=1,
            group_id=self.student_cohort.id,
            group_name=self.student_cohort.name,
            is_commentable_divided=True
        )

    def test_html(self, mock_request):
        _mock_text, mock_thread_id = self._create_mock_cohorted_thread(mock_request)

        self.client.login(username=self.student.username, password=self.TEST_PASSWORD)
        response = self.client.get(
            reverse('single_thread', kwargs={
                'course_id': str(self.course.id),
                'discussion_id': "cohorted_topic",
                'thread_id': mock_thread_id,
            })
        )

        assert response.status_code == 200
        assert response['Content-Type'] == 'text/html; charset=utf-8'
        html = response.content.decode('utf-8')

        # Verify that the group name is correctly included in the HTML
        self.assertRegex(html, r'"group_name": "student_cohort"')


@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
class SingleThreadAccessTestCase(CohortedTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def setUp(self):
        super().setUp()
        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)

    def call_view(self, mock_request, commentable_id, user, group_id, thread_group_id=None, pass_group_id=True):  # lint-amnesty, pylint: disable=missing-function-docstring
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text="dummy context", thread_id=thread_id, group_id=thread_group_id
        )

        request_data = {}
        if pass_group_id:
            request_data["group_id"] = group_id
        request = RequestFactory().get(
            "dummy_url",
            data=request_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        request.user = user
        return views.single_thread(
            request,
            str(self.course.id),
            commentable_id,
            thread_id
        )

    def test_student_non_cohorted(self, mock_request):
        resp = self.call_view(mock_request, "non_cohorted_topic", self.student, self.student_cohort.id)
        assert resp.status_code == 200

    def test_student_same_cohort(self, mock_request):
        resp = self.call_view(
            mock_request,
            "cohorted_topic",
            self.student,
            self.student_cohort.id,
            thread_group_id=self.student_cohort.id
        )
        assert resp.status_code == 200

    # this test ensures that a thread response from the cs with group_id: null
    # behaves the same as a thread response without a group_id (see: TNL-444)
    def test_student_global_thread_in_cohorted_topic(self, mock_request):
        resp = self.call_view(
            mock_request,
            "cohorted_topic",
            self.student,
            self.student_cohort.id,
            thread_group_id=None
        )
        assert resp.status_code == 200

    def test_student_different_cohort(self, mock_request):
        pytest.raises(Http404, (lambda: self.call_view(
            mock_request,
            'cohorted_topic',
            self.student,
            self.student_cohort.id,
            thread_group_id=self.moderator_cohort.id
        )))

    def test_moderator_non_cohorted(self, mock_request):
        resp = self.call_view(mock_request, "non_cohorted_topic", self.moderator, self.moderator_cohort.id)
        assert resp.status_code == 200

    def test_moderator_same_cohort(self, mock_request):
        resp = self.call_view(
            mock_request,
            "cohorted_topic",
            self.moderator,
            self.moderator_cohort.id,
            thread_group_id=self.moderator_cohort.id
        )
        assert resp.status_code == 200

    def test_moderator_different_cohort(self, mock_request):
        resp = self.call_view(
            mock_request,
            "cohorted_topic",
            self.moderator,
            self.moderator_cohort.id,
            thread_group_id=self.student_cohort.id
        )
        assert resp.status_code == 200

    def test_private_team_thread(self, mock_request):
        CourseTeamFactory.create(discussion_topic_id='dummy_discussion_id')
        user_not_in_team = UserFactory.create()
        CourseEnrollmentFactory(user=user_not_in_team, course_id=self.course.id)

        with patch('lms.djangoapps.teams.api.is_team_discussion_private', autospec=True) as mocked:
            mocked.return_value = True
            response = self.call_view(
                mock_request,
                'non_cohorted_topic',
                user_not_in_team,
                ''
            )
            assert 403 == response.status_code
            assert views.TEAM_PERMISSION_MESSAGE == response.content.decode('utf-8')


@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
class SingleThreadGroupIdTestCase(CohortedTestCase, GroupIdAssertionMixin):  # lint-amnesty, pylint: disable=missing-class-docstring
    cs_endpoint = "/threads/dummy_thread_id"

    def setUp(self):
        super().setUp()
        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)

    def call_view(self, mock_request, commentable_id, user, group_id, pass_group_id=True, is_ajax=False):  # lint-amnesty, pylint: disable=missing-function-docstring
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text="dummy context", group_id=self.student_cohort.id
        )

        request_data = {}
        if pass_group_id:
            request_data["group_id"] = group_id
        headers = {}
        if is_ajax:
            headers['HTTP_X_REQUESTED_WITH'] = "XMLHttpRequest"

        self.client.login(username=user.username, password=self.TEST_PASSWORD)

        return self.client.get(
            reverse('single_thread', args=[str(self.course.id), commentable_id, "dummy_thread_id"]),
            data=request_data,
            **headers
        )

    def test_group_info_in_html_response(self, mock_request):
        response = self.call_view(
            mock_request,
            "cohorted_topic",
            self.student,
            self.student_cohort.id,
            is_ajax=False
        )
        self._assert_html_response_contains_group_info(response)

    def test_group_info_in_ajax_response(self, mock_request):
        response = self.call_view(
            mock_request,
            "cohorted_topic",
            self.student,
            self.student_cohort.id,
            is_ajax=True
        )
        self._assert_json_response_contains_group_info(
            response, lambda d: d['content']
        )


@patch('requests.request', autospec=True)
class SingleThreadContentGroupTestCase(ForumsEnableMixin, UrlResetMixin, ContentGroupTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api.get_course_id_by_comment"
        )
        self.mock_get_course_id_by_comment = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)

    def assert_can_access(self, user, discussion_id, thread_id, should_have_access):
        """
        Verify that a user has access to a thread within a given
        discussion_id when should_have_access is True, otherwise
        verify that the user does not have access to that thread.
        """
        def call_single_thread():
            self.client.login(username=user.username, password=self.TEST_PASSWORD)
            return self.client.get(
                reverse('single_thread', args=[str(self.course.id), discussion_id, thread_id])
            )

        if should_have_access:
            assert call_single_thread().status_code == 200
        else:
            assert call_single_thread().status_code == 404

    def test_staff_user(self, mock_request):
        """
        Verify that the staff user can access threads in the alpha,
        beta, and global discussion blocks.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy content", thread_id=thread_id)

        for discussion_xblock in [self.alpha_block, self.beta_block, self.global_block]:
            self.assert_can_access(self.staff_user, discussion_xblock.discussion_id, thread_id, True)

    def test_alpha_user(self, mock_request):
        """
        Verify that the alpha user can access threads in the alpha and
        global discussion blocks.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy content", thread_id=thread_id)

        for discussion_xblock in [self.alpha_block, self.global_block]:
            self.assert_can_access(self.alpha_user, discussion_xblock.discussion_id, thread_id, True)

        self.assert_can_access(self.alpha_user, self.beta_block.discussion_id, thread_id, False)

    def test_beta_user(self, mock_request):
        """
        Verify that the beta user can access threads in the beta and
        global discussion blocks.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy content", thread_id=thread_id)

        for discussion_xblock in [self.beta_block, self.global_block]:
            self.assert_can_access(self.beta_user, discussion_xblock.discussion_id, thread_id, True)

        self.assert_can_access(self.beta_user, self.alpha_block.discussion_id, thread_id, False)

    def test_non_cohorted_user(self, mock_request):
        """
        Verify that the non-cohorted user can access threads in just the
        global discussion blocks.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy content", thread_id=thread_id)

        self.assert_can_access(self.non_cohorted_user, self.global_block.discussion_id, thread_id, True)

        self.assert_can_access(self.non_cohorted_user, self.alpha_block.discussion_id, thread_id, False)

        self.assert_can_access(self.non_cohorted_user, self.beta_block.discussion_id, thread_id, False)

    def test_course_context_respected(self, mock_request):
        """
        Verify that course threads go through discussion_category_id_access method.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text="dummy content", thread_id=thread_id
        )

        # Beta user does not have access to alpha_block.
        self.assert_can_access(self.beta_user, self.alpha_block.discussion_id, thread_id, False)

    def test_standalone_context_respected(self, mock_request):
        """
        Verify that standalone threads don't go through discussion_category_id_access method.
        """
        # For this rather pathological test, we are assigning the alpha block discussion_id (commentable_id)
        # to a team so that we can verify that standalone threads don't go through discussion_category_id_access.
        thread_id = "test_thread_id"
        CourseTeamFactory(
            name="A team",
            course_id=self.course.id,
            topic_id='topic_id',
            discussion_topic_id=self.alpha_block.discussion_id
        )
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text="dummy content", thread_id=thread_id,
            commentable_id=self.alpha_block.discussion_id
        )

        # If a thread returns context other than "course", the access check is not done, and the beta user
        # can see the alpha discussion block.
        self.assert_can_access(self.beta_user, self.alpha_block.discussion_id, thread_id, True)


@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
@patch('openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled', autospec=True)
class FollowedThreadsDiscussionGroupIdTestCase(CohortedTestCase, CohortedTopicGroupIdTestMixin):  # lint-amnesty, pylint: disable=missing-class-docstring
    cs_endpoint = "/subscribed_threads"

    def setUp(self):
        super().setUp()
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)

    def call_view(
        self,
        mock_is_forum_v2_enabled,
        mock_request,
        commentable_id,
        user,
        group_id,
        pass_group_id=True
    ):  # pylint: disable=arguments-differ
        mock_is_forum_v2_enabled.return_value = False
        kwargs = {}
        if group_id:
            kwargs['group_id'] = group_id
        mock_request.side_effect = make_mock_request_impl(self.course, "dummy content", **kwargs)

        request_data = {}
        if pass_group_id:
            request_data["group_id"] = group_id
        request = RequestFactory().get(
            "dummy_url",
            data=request_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        request.user = user
        return views.followed_threads(
            request,
            str(self.course.id),
            user.id
        )

    def test_group_info_in_ajax_response(self, mock_is_forum_v2_enabled, mock_request):
        response = self.call_view(
            mock_is_forum_v2_enabled,
            mock_request,
            "cohorted_topic",
            self.student,
            self.student_cohort.id
        )
        self._assert_json_response_contains_group_info(
            response, lambda d: d['discussion_data'][0]
        )


@patch('requests.request', autospec=True)
class CommentsServiceRequestHeadersTestCase(ForumsEnableMixin, UrlResetMixin, ModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    CREATE_USER = False

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api.get_course_id_by_comment"
        )
        self.mock_get_course_id_by_comment = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)

        username = "foo"
        password = "bar"

        # Invoke UrlResetMixin
        super().setUp()
        self.course = CourseFactory.create(discussion_topics={'dummy discussion': {'id': 'dummy_discussion_id'}})
        self.student = UserFactory.create(username=username, password=password)
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        assert self.client.login(username=username, password=password)

        self.addCleanup(translation.deactivate)

    def assert_all_calls_have_header(self, mock_request, key, value):  # lint-amnesty, pylint: disable=missing-function-docstring
        expected = call(
            ANY,  # method
            ANY,  # url
            data=ANY,
            params=ANY,
            headers=PartialDictMatcher({key: value}),
            timeout=ANY
        )
        for actual in mock_request.call_args_list:
            assert expected == actual

    def test_accept_language(self, mock_request):
        lang = "eo"
        text = "dummy content"
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text, thread_id=thread_id)

        self.client.get(
            reverse(
                "single_thread",
                kwargs={
                    "course_id": str(self.course.id),
                    "discussion_id": "dummy_discussion_id",
                    "thread_id": thread_id,
                }
            ),
            HTTP_ACCEPT_LANGUAGE=lang,
        )
        self.assert_all_calls_have_header(mock_request, "Accept-Language", lang)

    @override_settings(COMMENTS_SERVICE_KEY="test_api_key")
    def test_api_key(self, mock_request):
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy", thread_id="dummy")

        self.client.get(
            reverse(
                "forum_form_discussion",
                kwargs={"course_id": str(self.course.id)}
            ),
        )
        self.assert_all_calls_have_header(mock_request, "X-Edx-Api-Key", "test_api_key")


class SingleThreadUnicodeTestCase(ForumsEnableMixin, SharedModuleStoreTestCase, UnicodeTestMixin):  # lint-amnesty, pylint: disable=missing-class-docstring

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create(discussion_topics={'dummy_discussion_id': {'id': 'dummy_discussion_id'}})

    def setUp(self):
        super().setUp()
        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)

    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):  # lint-amnesty, pylint: disable=missing-function-docstring
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text, thread_id=thread_id)
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        # so (request.headers.get('x-requested-with') == 'XMLHttpRequest') == True
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"

        response = views.single_thread(request, str(self.course.id), "dummy_discussion_id", thread_id)
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data['content']['title'] == text
        assert response_data['content']['body'] == text


class UserProfileUnicodeTestCase(ForumsEnableMixin, SharedModuleStoreTestCase, UnicodeTestMixin):  # lint-amnesty, pylint: disable=missing-class-docstring

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)

    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):  # lint-amnesty, pylint: disable=missing-function-docstring
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text)
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        # so (request.headers.get('x-requested-with') == 'XMLHttpRequest') == True
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"

        response = views.user_profile(request, str(self.course.id), str(self.student.id))
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data['discussion_data'][0]['title'] == text
        assert response_data['discussion_data'][0]['body'] == text


class FollowedThreadsUnicodeTestCase(ForumsEnableMixin, SharedModuleStoreTestCase, UnicodeTestMixin):  # lint-amnesty, pylint: disable=missing-class-docstring

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)

    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):  # lint-amnesty, pylint: disable=missing-function-docstring
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text)
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        # so (request.headers.get('x-requested-with') == 'XMLHttpRequest') == True
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"

        response = views.followed_threads(request, str(self.course.id), str(self.student.id))
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data['discussion_data'][0]['title'] == text
        assert response_data['discussion_data'][0]['body'] == text


class EnrollmentTestCase(ForumsEnableMixin, ModuleStoreTestCase):
    """
    Tests for the behavior of views depending on if the student is enrolled
    in the course
    """

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()
        self.student = UserFactory.create()

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
    def test_unenrolled(self, mock_request):
        mock_request.side_effect = make_mock_request_impl(course=self.course, text='dummy')
        request = RequestFactory().get('dummy_url')
        request.user = self.student
        with pytest.raises(CourseAccessRedirect):
            views.forum_form_discussion(request, course_id=str(self.course.id))  # pylint: disable=no-value-for-parameter, unexpected-keyword-arg


class DividedDiscussionsTestCase(CohortViewsTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def create_divided_discussions(self):
        """
        Set up a divided discussion in the system, complete with all the fixings
        """
        divided_inline_discussions = ['Topic A']
        divided_course_wide_discussions = ["Topic B"]
        divided_discussions = divided_inline_discussions + divided_course_wide_discussions

        # inline discussion
        BlockFactory.create(
            parent_location=self.course.location,
            category="discussion",
            discussion_id=topic_name_to_id(self.course, "Topic A"),
            discussion_category="Chapter",
            discussion_target="Discussion",
            start=datetime.now()
        )
        # get updated course
        self.course = self.store.get_item(self.course.location)
        # course-wide discussion
        discussion_topics = {
            "Topic B": {"id": "Topic B"},
        }

        config_course_cohorts(
            self.course,
            is_cohorted=True,
        )

        config_course_discussions(
            self.course,
            discussion_topics=discussion_topics,
            divided_discussions=divided_discussions
        )
        return divided_inline_discussions, divided_course_wide_discussions


class CourseDiscussionTopicsTestCase(DividedDiscussionsTestCase):
    """
    Tests the `divide_discussion_topics` view.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def test_non_staff(self):
        """
        Verify that we cannot access divide_discussion_topics if we're a non-staff user.
        """
        self._verify_non_staff_cannot_access(views.discussion_topics, "GET", [str(self.course.id)])

    def test_get_discussion_topics(self):
        """
        Verify that discussion_topics is working for HTTP GET.
        """
        # create inline & course-wide discussion to verify the different map.
        self.create_divided_discussions()

        response = self.get_handler(self.course, handler=views.discussion_topics)
        start_date = response['inline_discussions']['subcategories']['Chapter']['start_date']
        expected_response = {
            "course_wide_discussions": {
                'children': [['Topic B', TYPE_ENTRY]],
                'entries': {
                    'Topic B': {
                        'sort_key': 'A',
                        'is_divided': True,
                        'id': topic_name_to_id(self.course, "Topic B"),
                        'start_date': response['course_wide_discussions']['entries']['Topic B']['start_date']
                    }
                }
            },
            "inline_discussions": {
                'subcategories': {
                    'Chapter': {
                        'subcategories': {},
                        'children': [['Discussion', TYPE_ENTRY]],
                        'entries': {
                            'Discussion': {
                                'sort_key': None,
                                'is_divided': True,
                                'id': topic_name_to_id(self.course, "Topic A"),
                                'start_date': start_date
                            }
                        },
                        'sort_key': 'Chapter',
                        'start_date': start_date
                    }
                },
                'children': [['Chapter', TYPE_SUBCATEGORY]]
            }
        }
        assert response == expected_response


class CourseDiscussionsHandlerTestCase(DividedDiscussionsTestCase):
    """
    Tests the course_discussion_settings_handler
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def get_expected_response(self):
        """
        Returns the static response dict.
        """
        return {
            'always_divide_inline_discussions': False,
            'divided_inline_discussions': [],
            'divided_course_wide_discussions': [],
            'id': 1,
            'division_scheme': 'cohort',
            'available_division_schemes': ['cohort']
        }

    def test_non_staff(self):
        """
        Verify that we cannot access course_discussions_settings_handler if we're a non-staff user.
        """
        self._verify_non_staff_cannot_access(
            course_discussions_settings_handler, "GET", [str(self.course.id)]
        )
        self._verify_non_staff_cannot_access(
            course_discussions_settings_handler, "PATCH", [str(self.course.id)]
        )

    def test_update_always_divide_inline_discussion_settings(self):
        """
        Verify that course_discussions_settings_handler is working for always_divide_inline_discussions via HTTP PATCH.
        """
        config_course_cohorts(self.course, is_cohorted=True)

        response = self.get_handler(self.course, handler=course_discussions_settings_handler)

        expected_response = self.get_expected_response()

        assert response == expected_response

        expected_response['always_divide_inline_discussions'] = True
        response = self.patch_handler(
            self.course, data=expected_response, handler=course_discussions_settings_handler
        )

        assert response == expected_response

    def test_update_course_wide_discussion_settings(self):
        """
        Verify that course_discussions_settings_handler is working for divided_course_wide_discussions via HTTP PATCH.
        """
        # course-wide discussion
        discussion_topics = {
            "Topic B": {"id": "Topic B"},
        }

        config_course_cohorts(self.course, is_cohorted=True)
        config_course_discussions(self.course, discussion_topics=discussion_topics)

        response = self.get_handler(self.course, handler=views.course_discussions_settings_handler)

        expected_response = self.get_expected_response()
        assert response == expected_response

        expected_response['divided_course_wide_discussions'] = [topic_name_to_id(self.course, "Topic B")]
        response = self.patch_handler(
            self.course, data=expected_response, handler=views.course_discussions_settings_handler
        )

        assert response == expected_response

    def test_update_inline_discussion_settings(self):
        """
        Verify that course_discussions_settings_handler is working for divided_inline_discussions via HTTP PATCH.
        """
        config_course_cohorts(self.course, is_cohorted=True)

        response = self.get_handler(self.course, handler=views.course_discussions_settings_handler)

        expected_response = self.get_expected_response()
        assert response == expected_response

        RequestCache.clear_all_namespaces()
        now = datetime.now()
        # inline discussion
        BlockFactory.create(
            parent_location=self.course.location,
            category="discussion",
            discussion_id="Topic_A",
            discussion_category="Chapter",
            discussion_target="Discussion",
            start=now
        )

        expected_response['divided_inline_discussions'] = ["Topic_A"]
        response = self.patch_handler(
            self.course, data=expected_response, handler=views.course_discussions_settings_handler
        )

        assert response == expected_response

    def test_get_settings(self):
        """
        Verify that course_discussions_settings_handler is working for HTTP GET.
        """
        divided_inline_discussions, divided_course_wide_discussions = self.create_divided_discussions()

        response = self.get_handler(self.course, handler=views.course_discussions_settings_handler)
        expected_response = self.get_expected_response()

        expected_response['divided_inline_discussions'] = [topic_name_to_id(self.course, name)
                                                           for name in divided_inline_discussions]
        expected_response['divided_course_wide_discussions'] = [topic_name_to_id(self.course, name)
                                                                for name in divided_course_wide_discussions]

        assert response == expected_response

    def test_update_settings_with_invalid_field_data_type(self):
        """
        Verify that course_discussions_settings_handler return HTTP 400 if field data type is incorrect.
        """
        config_course_cohorts(self.course, is_cohorted=True)

        response = self.patch_handler(
            self.course,
            data={'always_divide_inline_discussions': ''},
            expected_response_code=400,
            handler=views.course_discussions_settings_handler
        )
        assert 'Incorrect field type for `{}`. Type must be `{}`'.format(
            'always_divide_inline_discussions',
            bool.__name__
        ) == response.get('error')

    def test_available_schemes(self):
        # Cohorts disabled, single enrollment mode.
        config_course_cohorts(self.course, is_cohorted=False)
        response = self.get_handler(self.course, handler=views.course_discussions_settings_handler)
        expected_response = self.get_expected_response()
        expected_response['available_division_schemes'] = []
        assert response == expected_response

        # Add 2 enrollment modes
        CourseModeFactory.create(course_id=self.course.id, mode_slug=CourseMode.AUDIT)
        CourseModeFactory.create(course_id=self.course.id, mode_slug=CourseMode.VERIFIED)
        response = self.get_handler(self.course, handler=views.course_discussions_settings_handler)
        expected_response['available_division_schemes'] = [CourseDiscussionSettings.ENROLLMENT_TRACK]
        assert response == expected_response

        # Enable cohorts
        config_course_cohorts(self.course, is_cohorted=True)
        response = self.get_handler(self.course, handler=views.course_discussions_settings_handler)
        expected_response['available_division_schemes'] = [
            CourseDiscussionSettings.COHORT, CourseDiscussionSettings.ENROLLMENT_TRACK
        ]
        assert response == expected_response


class DefaultTopicIdGetterTestCase(ModuleStoreTestCase):
    """
    Tests the `_get_discussion_default_topic_id` helper.
    """

    def test_no_default_topic(self):
        discussion_topics = {
            'dummy discussion': {
                'id': 'dummy_discussion_id',
            },
        }
        course = CourseFactory.create(discussion_topics=discussion_topics)
        expected_id = None
        result = _get_discussion_default_topic_id(course)
        assert expected_id == result

    def test_default_topic_id(self):
        discussion_topics = {
            'dummy discussion': {
                'id': 'dummy_discussion_id',
            },
            'another discussion': {
                'id': 'another_discussion_id',
                'default': True,
            },
        }
        course = CourseFactory.create(discussion_topics=discussion_topics)
        expected_id = 'another_discussion_id'
        result = _get_discussion_default_topic_id(course)
        assert expected_id == result


class ThreadViewedEventTestCase(EventTestMixin, ForumsEnableMixin, UrlResetMixin, ModuleStoreTestCase):
    """
    Forum thread views are expected to launch analytics events. Test these here.
    """

    CATEGORY_ID = 'i4x-edx-discussion-id'
    CATEGORY_NAME = 'Discussion 1'
    PARENT_CATEGORY_NAME = 'Chapter 1'

    DUMMY_THREAD_ID = 'dummythreadids'
    DUMMY_TITLE = 'Dummy title'
    DUMMY_URL = 'https://example.com/dummy/url/'

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp('lms.djangoapps.discussion.django_comment_client.base.views.tracker')

        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)
        self.course = CourseFactory.create(
            teams_configuration=TeamsConfig({
                'topics': [{
                    'id': 'arbitrary-topic-id',
                    'name': 'arbitrary-topic-name',
                    'description': 'arbitrary-topic-desc'
                }]
            })
        )
        seed_permissions_roles(self.course.id)

        PASSWORD = 'test'
        self.student = UserFactory.create(password=PASSWORD)
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

        self.staff = UserFactory.create(is_staff=True)
        UserBasedRole(user=self.staff, role=CourseStaffRole.ROLE).add_course(self.course.id)

        self.category = BlockFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id=self.CATEGORY_ID,
            discussion_category=self.PARENT_CATEGORY_NAME,
            discussion_target=self.CATEGORY_NAME,
        )
        self.team = CourseTeamFactory.create(
            name='Team 1',
            course_id=self.course.id,
            topic_id='arbitrary-topic-id',
            discussion_topic_id=self.category.discussion_id,
        )
        CourseTeamMembershipFactory.create(team=self.team, user=self.student)
        self.client.login(username=self.student.username, password=PASSWORD)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    @patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.perform_request')
    def test_thread_viewed_event(self, mock_perform_request):
        mock_perform_request.side_effect = make_mock_perform_request_impl(
            course=self.course,
            text=self.DUMMY_TITLE,
            thread_id=self.DUMMY_THREAD_ID,
            commentable_id=self.category.discussion_id,
        )
        url = '/courses/{}/discussion/forum/{}/threads/{}'.format(
            str(self.course.id),
            self.category.discussion_id,
            self.DUMMY_THREAD_ID
        )
        self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        expected_event = {
            'id': self.DUMMY_THREAD_ID,
            'title': self.DUMMY_TITLE,
            'commentable_id': self.category.discussion_id,
            'category_id': self.category.discussion_id,
            'category_name': self.category.discussion_target,
            'user_forums_roles': [FORUM_ROLE_STUDENT],
            'user_course_roles': [],
            'target_username': self.student.username,
            'team_id': self.team.id,
            'url': self.DUMMY_URL,
        }
        expected_event_items = list(expected_event.items())

        self.assert_event_emission_count('edx.forum.thread.viewed', 1)
        _, event = self.get_latest_call_args()
        event_items = list(event.items())
        assert ((kv_pair in event_items) for kv_pair in expected_event_items)


@ddt.ddt
@patch(
    'openedx.core.djangoapps.django_comment_common.comment_client.utils.perform_request',
    Mock(
        return_value={
            "id": "test_thread",
            "title": "Title",
            "body": "<p></p>",
            "default_sort_key": "date",
            "upvoted_ids": [],
            "downvoted_ids": [],
            "subscribed_thread_ids": [],
        }
    )
)
class ForumMFETestCase(ForumsEnableMixin, SharedModuleStoreTestCase):
    """
    Tests that the MFE upgrade banner and MFE is shown in the correct situation with the correct UI
    """

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create()
        self.staff_user = AdminFactory.create()
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

    @override_settings(DISCUSSIONS_MICROFRONTEND_URL="http://test.url")
    def test_redirect_from_legacy_base_url_to_new_experience(self):
        """
        Verify that the legacy url is redirected to MFE homepage when
        ENABLE_DISCUSSIONS_MFE flag is enabled.
        """

        with override_waffle_flag(ENABLE_DISCUSSIONS_MFE, True):
            self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
            url = reverse("forum_form_discussion", args=[self.course.id])
            response = self.client.get(url)
            assert response.status_code == 302
            expected_url = f"{settings.DISCUSSIONS_MICROFRONTEND_URL}/{str(self.course.id)}"
            assert response.url == expected_url

    @override_settings(DISCUSSIONS_MICROFRONTEND_URL="http://test.url")
    def test_redirect_from_legacy_profile_url_to_new_experience(self):
        """
        Verify that the requested user profile is redirected to MFE learners tab when
        ENABLE_DISCUSSIONS_MFE flag is enabled
        """

        with override_waffle_flag(ENABLE_DISCUSSIONS_MFE, True):
            self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
            url = reverse("user_profile", args=[self.course.id, self.user.id])
            response = self.client.get(url)
            assert response.status_code == 302
            expected_url = f"{settings.DISCUSSIONS_MICROFRONTEND_URL}/{str(self.course.id)}/learners"
            assert response.url == expected_url

    @override_settings(DISCUSSIONS_MICROFRONTEND_URL="http://test.url")
    def test_redirect_from_legacy_single_thread_to_new_experience(self):
        """
        Verify that a legacy single url is redirected to corresponding MFE thread url when the ENABLE_DISCUSSIONS_MFE
        flag is enabled
        """

        with override_waffle_flag(ENABLE_DISCUSSIONS_MFE, True):
            self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
            url = reverse("single_thread", args=[self.course.id, "test_discussion", "test_thread"])
            response = self.client.get(url)
            assert response.status_code == 302
            expected_url = f"{settings.DISCUSSIONS_MICROFRONTEND_URL}/{str(self.course.id)}/posts/test_thread"
            assert response.url == expected_url

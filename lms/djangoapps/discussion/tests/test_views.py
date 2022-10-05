"""
Tests the forum notification views.
"""
import json
import logging
from datetime import datetime
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
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_MONGO_AMNESTY_MODULESTORE,
    ModuleStoreTestCase,
    SharedModuleStoreTestCase
)
from xmodule.modulestore.tests.factories import (
    CourseFactory,
    ItemFactory,
    check_mongo_calls
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
    NonCohortedTopicGroupIdTestMixin
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
from openedx.core.djangoapps.course_groups.models import CourseUserGroup
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
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.enterprise_support.tests.mixins.enterprise import EnterpriseTestConsentRequired

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
        with patch('common.djangoapps.student.models.cc.User.save'):
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

    @patch('common.djangoapps.student.models.cc.User.from_django_user')
    @patch('common.djangoapps.student.models.cc.User.active_threads')
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

    @patch('common.djangoapps.student.models.cc.User.from_django_user')
    @patch('common.djangoapps.student.models.cc.User.subscribed_threads')
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
        self.client.login(username=user_not_in_team.username, password='test')

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


@ddt.ddt
@patch('requests.request', autospec=True)
class SingleThreadQueryCountTestCase(ForumsEnableMixin, ModuleStoreTestCase):
    """
    Ensures the number of modulestore queries and number of sql queries are
    independent of the number of responses retrieved for a given discussion thread.
    """
    @ddt.data(
        # split mongo: 3 queries, regardless of thread response size.
        (False, 1, 2, 2, 21, 8),
        (False, 50, 2, 2, 21, 8),

        # Enabling Enterprise integration should have no effect on the number of mongo queries made.
        # split mongo: 3 queries, regardless of thread response size.
        (True, 1, 2, 2, 21, 8),
        (True, 50, 2, 2, 21, 8),
    )
    @ddt.unpack
    def test_number_of_mongo_queries(
            self,
            enterprise_enabled,
            num_thread_responses,
            num_uncached_mongo_calls,
            num_cached_mongo_calls,
            num_uncached_sql_queries,
            num_cached_sql_queries,
            mock_request
    ):
        ContentTypeGatingConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))
        with modulestore().default_store(ModuleStoreEnum.Type.split):
            course = CourseFactory.create(discussion_topics={'dummy discussion': {'id': 'dummy_discussion_id'}})

        student = UserFactory.create()
        CourseEnrollmentFactory.create(user=student, course_id=course.id)

        test_thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(
            course=course, text="dummy content", thread_id=test_thread_id, num_thread_responses=num_thread_responses
        )
        request = RequestFactory().get(
            "dummy_url",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        request.user = student

        def call_single_thread():
            """
            Call single_thread and assert that it returns what we expect.
            """
            with patch.dict("django.conf.settings.FEATURES", dict(ENABLE_ENTERPRISE_INTEGRATION=enterprise_enabled)):
                response = views.single_thread(
                    request,
                    str(course.id),
                    "dummy_discussion_id",
                    test_thread_id
                )
            assert response.status_code == 200
            assert len(json.loads(response.content.decode('utf-8'))['content']['children']) == num_thread_responses

        # Test uncached first, then cached now that the cache is warm.
        cached_calls = [
            [num_uncached_mongo_calls, num_uncached_sql_queries],
            # Sometimes there will be one more or fewer sql call than expected, because the call to
            # CourseMode.modes_for_course sometimes does / doesn't get cached and does / doesn't hit the DB.
            # EDUCATOR-5167
            [num_cached_mongo_calls, AllowPlusOrMinusOneInt(num_cached_sql_queries)],
        ]
        for expected_mongo_calls, expected_sql_queries in cached_calls:
            with self.assertNumQueries(expected_sql_queries, table_ignorelist=QUERY_COUNT_TABLE_IGNORELIST):
                with check_mongo_calls(expected_mongo_calls):
                    call_single_thread()


@patch('requests.request', autospec=True)
class SingleCohortedThreadTestCase(CohortedTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

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

        self.client.login(username=self.student.username, password='test')
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

        self.client.login(username=user.username, password='test')

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
class ForumFormDiscussionContentGroupTestCase(ForumsEnableMixin, ContentGroupTestCase):
    """
    Tests `forum_form_discussion api` works with different content groups.
    Discussion modules are setup in ContentGroupTestCase class i.e
    alpha_module => alpha_group_discussion => alpha_cohort => alpha_user/community_ta
    beta_module => beta_group_discussion => beta_cohort => beta_user
    """

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        self.thread_list = [
            {"thread_id": "test_general_thread_id"},
            {"thread_id": "test_global_group_thread_id", "commentable_id": self.global_module.discussion_id},
            {"thread_id": "test_alpha_group_thread_id", "group_id": self.alpha_module.group_access[0][0],
             "commentable_id": self.alpha_module.discussion_id},
            {"thread_id": "test_beta_group_thread_id", "group_id": self.beta_module.group_access[0][0],
             "commentable_id": self.beta_module.discussion_id}
        ]

    def assert_has_access(self, response, expected_discussion_threads):
        """
        Verify that a users have access to the threads in their assigned
        cohorts and non-cohorted modules.
        """
        discussion_data = json.loads(response.content.decode('utf-8'))['discussion_data']
        assert len(discussion_data) == expected_discussion_threads

    def call_view(self, mock_request, user):  # lint-amnesty, pylint: disable=missing-function-docstring
        mock_request.side_effect = make_mock_request_impl(
            course=self.course,
            text="dummy content",
            thread_list=self.thread_list
        )
        self.client.login(username=user.username, password='test')
        return self.client.get(
            reverse("forum_form_discussion", args=[str(self.course.id)]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

    def test_community_ta_user(self, mock_request):
        """
        Verify that community_ta user has access to all threads regardless
        of cohort.
        """
        response = self.call_view(
            mock_request,
            self.community_ta
        )
        self.assert_has_access(response, 4)

    def test_alpha_cohort_user(self, mock_request):
        """
        Verify that alpha_user has access to alpha_cohort and non-cohorted
        threads.
        """
        response = self.call_view(
            mock_request,
            self.alpha_user
        )
        self.assert_has_access(response, 3)

    def test_beta_cohort_user(self, mock_request):
        """
        Verify that beta_user has access to beta_cohort and non-cohorted
        threads.
        """
        response = self.call_view(
            mock_request,
            self.beta_user
        )
        self.assert_has_access(response, 3)

    def test_global_staff_user(self, mock_request):
        """
        Verify that global staff user has access to all threads regardless
        of cohort.
        """
        response = self.call_view(
            mock_request,
            self.staff_user
        )
        self.assert_has_access(response, 4)


@patch('requests.request', autospec=True)
class SingleThreadContentGroupTestCase(ForumsEnableMixin, UrlResetMixin, ContentGroupTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()

    def assert_can_access(self, user, discussion_id, thread_id, should_have_access):
        """
        Verify that a user has access to a thread within a given
        discussion_id when should_have_access is True, otherwise
        verify that the user does not have access to that thread.
        """
        def call_single_thread():
            self.client.login(username=user.username, password='test')
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
        beta, and global discussion modules.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy content", thread_id=thread_id)

        for discussion_xblock in [self.alpha_module, self.beta_module, self.global_module]:
            self.assert_can_access(self.staff_user, discussion_xblock.discussion_id, thread_id, True)

    def test_alpha_user(self, mock_request):
        """
        Verify that the alpha user can access threads in the alpha and
        global discussion modules.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy content", thread_id=thread_id)

        for discussion_xblock in [self.alpha_module, self.global_module]:
            self.assert_can_access(self.alpha_user, discussion_xblock.discussion_id, thread_id, True)

        self.assert_can_access(self.alpha_user, self.beta_module.discussion_id, thread_id, False)

    def test_beta_user(self, mock_request):
        """
        Verify that the beta user can access threads in the beta and
        global discussion modules.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy content", thread_id=thread_id)

        for discussion_xblock in [self.beta_module, self.global_module]:
            self.assert_can_access(self.beta_user, discussion_xblock.discussion_id, thread_id, True)

        self.assert_can_access(self.beta_user, self.alpha_module.discussion_id, thread_id, False)

    def test_non_cohorted_user(self, mock_request):
        """
        Verify that the non-cohorted user can access threads in just the
        global discussion module.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy content", thread_id=thread_id)

        self.assert_can_access(self.non_cohorted_user, self.global_module.discussion_id, thread_id, True)

        self.assert_can_access(self.non_cohorted_user, self.alpha_module.discussion_id, thread_id, False)

        self.assert_can_access(self.non_cohorted_user, self.beta_module.discussion_id, thread_id, False)

    def test_course_context_respected(self, mock_request):
        """
        Verify that course threads go through discussion_category_id_access method.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text="dummy content", thread_id=thread_id
        )

        # Beta user does not have access to alpha_module.
        self.assert_can_access(self.beta_user, self.alpha_module.discussion_id, thread_id, False)

    def test_standalone_context_respected(self, mock_request):
        """
        Verify that standalone threads don't go through discussion_category_id_access method.
        """
        # For this rather pathological test, we are assigning the alpha module discussion_id (commentable_id)
        # to a team so that we can verify that standalone threads don't go through discussion_category_id_access.
        thread_id = "test_thread_id"
        CourseTeamFactory(
            name="A team",
            course_id=self.course.id,
            topic_id='topic_id',
            discussion_topic_id=self.alpha_module.discussion_id
        )
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text="dummy content", thread_id=thread_id,
            commentable_id=self.alpha_module.discussion_id
        )

        # If a thread returns context other than "course", the access check is not done, and the beta user
        # can see the alpha discussion module.
        self.assert_can_access(self.beta_user, self.alpha_module.discussion_id, thread_id, True)


@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
class InlineDiscussionContextTestCase(ForumsEnableMixin, ModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id)
        self.discussion_topic_id = "dummy_topic"
        self.team = CourseTeamFactory(
            name="A team",
            course_id=self.course.id,
            topic_id='topic_id',
            discussion_topic_id=self.discussion_topic_id
        )

        self.team.add_user(self.user)
        self.user_not_in_team = UserFactory.create()

    def test_context_can_be_standalone(self, mock_request):
        mock_request.side_effect = make_mock_request_impl(
            course=self.course,
            text="dummy text",
            commentable_id=self.discussion_topic_id
        )

        request = RequestFactory().get("dummy_url")
        request.user = self.user

        response = views.inline_discussion(
            request,
            str(self.course.id),
            self.discussion_topic_id,
        )

        json_response = json.loads(response.content.decode('utf-8'))
        assert json_response['discussion_data'][0]['context'] == ThreadContext.STANDALONE

    def test_private_team_discussion(self, mock_request):
        # First set the team discussion to be private
        CourseEnrollmentFactory(user=self.user_not_in_team, course_id=self.course.id)
        request = RequestFactory().get("dummy_url")
        request.user = self.user_not_in_team

        mock_request.side_effect = make_mock_request_impl(
            course=self.course,
            text="dummy text",
            commentable_id=self.discussion_topic_id
        )

        with patch('lms.djangoapps.teams.api.is_team_discussion_private', autospec=True) as mocked:
            mocked.return_value = True
            response = views.inline_discussion(
                request,
                str(self.course.id),
                self.discussion_topic_id,
            )
            assert response.status_code == 403
            assert response.content.decode('utf-8') == views.TEAM_PERMISSION_MESSAGE


@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
class InlineDiscussionGroupIdTestCase(  # lint-amnesty, pylint: disable=missing-class-docstring
        CohortedTestCase,
        CohortedTopicGroupIdTestMixin,
        NonCohortedTopicGroupIdTestMixin
):
    cs_endpoint = "/threads"

    def setUp(self):
        super().setUp()
        self.cohorted_commentable_id = 'cohorted_topic'

    def call_view(self, mock_request, commentable_id, user, group_id, pass_group_id=True):
        kwargs = {'commentable_id': self.cohorted_commentable_id}
        if group_id:
            # avoid causing a server error when the LMS chokes attempting
            # to find a group name for the group_id, when we're testing with
            # an invalid one.
            try:
                CourseUserGroup.objects.get(id=group_id)
                kwargs['group_id'] = group_id
            except CourseUserGroup.DoesNotExist:
                pass
        mock_request.side_effect = make_mock_request_impl(self.course, "dummy content", **kwargs)

        request_data = {}
        if pass_group_id:
            request_data["group_id"] = group_id
        request = RequestFactory().get(
            "dummy_url",
            data=request_data
        )
        request.user = user
        return views.inline_discussion(
            request,
            str(self.course.id),
            commentable_id
        )

    def test_group_info_in_ajax_response(self, mock_request):
        response = self.call_view(
            mock_request,
            self.cohorted_commentable_id,
            self.student,
            self.student_cohort.id
        )
        self._assert_json_response_contains_group_info(
            response, lambda d: d['discussion_data'][0]
        )


@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
class ForumFormDiscussionGroupIdTestCase(CohortedTestCase, CohortedTopicGroupIdTestMixin):  # lint-amnesty, pylint: disable=missing-class-docstring
    cs_endpoint = "/threads"

    def call_view(self, mock_request, commentable_id, user, group_id, pass_group_id=True, is_ajax=False):  # pylint: disable=arguments-differ
        kwargs = {}
        if group_id:
            kwargs['group_id'] = group_id
        mock_request.side_effect = make_mock_request_impl(self.course, "dummy content", **kwargs)

        request_data = {}
        if pass_group_id:
            request_data["group_id"] = group_id
        headers = {}
        if is_ajax:
            headers['HTTP_X_REQUESTED_WITH'] = "XMLHttpRequest"

        self.client.login(username=user.username, password='test')
        return self.client.get(
            reverse("forum_form_discussion", args=[str(self.course.id)]),
            data=request_data,
            **headers
        )

    def test_group_info_in_html_response(self, mock_request):
        response = self.call_view(
            mock_request,
            "cohorted_topic",
            self.student,
            self.student_cohort.id
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
            response, lambda d: d['discussion_data'][0]
        )


@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
class UserProfileDiscussionGroupIdTestCase(CohortedTestCase, CohortedTopicGroupIdTestMixin):  # lint-amnesty, pylint: disable=missing-class-docstring
    cs_endpoint = "/active_threads"

    def call_view_for_profiled_user(
            self, mock_request, requesting_user, profiled_user, group_id, pass_group_id, is_ajax=False
    ):
        """
        Calls "user_profile" view method on behalf of "requesting_user" to get information about
        the user "profiled_user".
        """
        kwargs = {}
        if group_id:
            kwargs['group_id'] = group_id
        mock_request.side_effect = make_mock_request_impl(self.course, "dummy content", **kwargs)

        request_data = {}
        if pass_group_id:
            request_data["group_id"] = group_id
        headers = {}
        if is_ajax:
            headers['HTTP_X_REQUESTED_WITH'] = "XMLHttpRequest"

        self.client.login(username=requesting_user.username, password='test')
        return self.client.get(
            reverse('user_profile', args=[str(self.course.id), profiled_user.id]),
            data=request_data,
            **headers
        )

    def call_view(self, mock_request, _commentable_id, user, group_id, pass_group_id=True, is_ajax=False):  # pylint: disable=arguments-differ
        return self.call_view_for_profiled_user(
            mock_request, user, user, group_id, pass_group_id=pass_group_id, is_ajax=is_ajax
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
            response, lambda d: d['discussion_data'][0]
        )

    def _test_group_id_passed_to_user_profile(
            self, mock_request, expect_group_id_in_request, requesting_user, profiled_user, group_id, pass_group_id
    ):
        """
        Helper method for testing whether or not group_id was passed to the user_profile request.
        """

        def get_params_from_user_info_call(for_specific_course):
            """
            Returns the request parameters for the user info call with either course_id specified or not,
            depending on value of 'for_specific_course'.
            """
            # There will be 3 calls from user_profile. One has the cs_endpoint "active_threads", and it is already
            # tested. The other 2 calls are for user info; one of those calls is for general information about the user,
            # and it does not specify a course_id. The other call does specify a course_id, and if the caller did not
            # have discussion moderator privileges, it should also contain a group_id.
            for r_call in mock_request.call_args_list:
                if not r_call[0][1].endswith(self.cs_endpoint):
                    params = r_call[1]["params"]
                    has_course_id = "course_id" in params
                    if (for_specific_course and has_course_id) or (not for_specific_course and not has_course_id):
                        return params
            pytest.fail("Did not find appropriate user_profile call for 'for_specific_course'=" + for_specific_course)

        mock_request.reset_mock()
        self.call_view_for_profiled_user(
            mock_request,
            requesting_user,
            profiled_user,
            group_id,
            pass_group_id=pass_group_id,
            is_ajax=False
        )
        # Should never have a group_id if course_id was not included in the request.
        params_without_course_id = get_params_from_user_info_call(False)
        assert 'group_id' not in params_without_course_id

        params_with_course_id = get_params_from_user_info_call(True)
        if expect_group_id_in_request:
            assert 'group_id' in params_with_course_id
            assert group_id == params_with_course_id['group_id']
        else:
            assert 'group_id' not in params_with_course_id

    def test_group_id_passed_to_user_profile_student(self, mock_request):
        """
        Test that the group id is always included when requesting user profile information for a particular
        course if the requester does not have discussion moderation privileges.
        """
        def verify_group_id_always_present(profiled_user, pass_group_id):
            """
            Helper method to verify that group_id is always present for student in course
            (non-privileged user).
            """
            self._test_group_id_passed_to_user_profile(
                mock_request, True, self.student, profiled_user, self.student_cohort.id, pass_group_id
            )

        # In all these test cases, the requesting_user is the student (non-privileged user).
        # The profile returned on behalf of the student is for the profiled_user.
        verify_group_id_always_present(profiled_user=self.student, pass_group_id=True)
        verify_group_id_always_present(profiled_user=self.student, pass_group_id=False)
        verify_group_id_always_present(profiled_user=self.moderator, pass_group_id=True)
        verify_group_id_always_present(profiled_user=self.moderator, pass_group_id=False)

    def test_group_id_user_profile_moderator(self, mock_request):
        """
        Test that the group id is only included when a privileged user requests user profile information for a
        particular course and user if the group_id is explicitly passed in.
        """
        def verify_group_id_present(profiled_user, pass_group_id, requested_cohort=self.moderator_cohort):
            """
            Helper method to verify that group_id is present.
            """
            self._test_group_id_passed_to_user_profile(
                mock_request, True, self.moderator, profiled_user, requested_cohort.id, pass_group_id
            )

        def verify_group_id_not_present(profiled_user, pass_group_id, requested_cohort=self.moderator_cohort):
            """
            Helper method to verify that group_id is not present.
            """
            self._test_group_id_passed_to_user_profile(
                mock_request, False, self.moderator, profiled_user, requested_cohort.id, pass_group_id
            )

        # In all these test cases, the requesting_user is the moderator (privileged user).

        # If the group_id is explicitly passed, it will be present in the request.
        verify_group_id_present(profiled_user=self.student, pass_group_id=True)
        verify_group_id_present(profiled_user=self.moderator, pass_group_id=True)
        verify_group_id_present(
            profiled_user=self.student, pass_group_id=True, requested_cohort=self.student_cohort
        )

        # If the group_id is not explicitly passed, it will not be present because the requesting_user
        # has discussion moderator privileges.
        verify_group_id_not_present(profiled_user=self.student, pass_group_id=False)
        verify_group_id_not_present(profiled_user=self.moderator, pass_group_id=False)


@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
class FollowedThreadsDiscussionGroupIdTestCase(CohortedTestCase, CohortedTopicGroupIdTestMixin):  # lint-amnesty, pylint: disable=missing-class-docstring
    cs_endpoint = "/subscribed_threads"

    def call_view(self, mock_request, commentable_id, user, group_id, pass_group_id=True):
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

    def test_group_info_in_ajax_response(self, mock_request):
        response = self.call_view(
            mock_request,
            "cohorted_topic",
            self.student,
            self.student_cohort.id
        )
        self._assert_json_response_contains_group_info(
            response, lambda d: d['discussion_data'][0]
        )


@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
class InlineDiscussionTestCase(ForumsEnableMixin, ModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def setUp(self):
        super().setUp()

        self.course = CourseFactory.create(
            org="TestX",
            number="101",
            display_name="Test Course",
            teams_configuration=TeamsConfig({
                'topics': [{
                    'id': 'topic_id',
                    'name': 'A topic',
                    'description': 'A topic',
                }]
            })
        )
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)
        self.discussion1 = ItemFactory.create(
            parent_location=self.course.location,
            category="discussion",
            discussion_id="discussion1",
            display_name='Discussion1',
            discussion_category="Chapter",
            discussion_target="Discussion1"
        )

    def send_request(self, mock_request, params=None):
        """
        Creates and returns a request with params set, and configures
        mock_request to return appropriate values.
        """
        request = RequestFactory().get("dummy_url", params if params else {})
        request.user = self.student
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text="dummy content", commentable_id=self.discussion1.discussion_id
        )
        return views.inline_discussion(
            request, str(self.course.id), self.discussion1.discussion_id
        )

    def test_context(self, mock_request):
        team = CourseTeamFactory(
            name='Team Name',
            topic_id='topic_id',
            course_id=self.course.id,
            discussion_topic_id=self.discussion1.discussion_id
        )

        team.add_user(self.student)

        self.send_request(mock_request)
        assert mock_request.call_args[1]['params']['context'] == ThreadContext.STANDALONE


@patch('requests.request', autospec=True)
class UserProfileTestCase(ForumsEnableMixin, UrlResetMixin, ModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    TEST_THREAD_TEXT = 'userprofile-test-text'
    TEST_THREAD_ID = 'userprofile-test-thread-id'

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()

        self.course = CourseFactory.create()
        self.student = UserFactory.create()
        self.profiled_user = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        CourseEnrollmentFactory.create(user=self.profiled_user, course_id=self.course.id)

    def get_response(self, mock_request, params, **headers):  # lint-amnesty, pylint: disable=missing-function-docstring
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text=self.TEST_THREAD_TEXT, thread_id=self.TEST_THREAD_ID
        )
        self.client.login(username=self.student.username, password='test')

        response = self.client.get(
            reverse('user_profile', kwargs={
                'course_id': str(self.course.id),
                'user_id': self.profiled_user.id,
            }),
            data=params,
            **headers
        )
        mock_request.assert_any_call(
            "get",
            StringEndsWithMatcher(f'/users/{self.profiled_user.id}/active_threads'),
            data=None,
            params=PartialDictMatcher({
                "course_id": str(self.course.id),
                "page": params.get("page", 1),
                "per_page": views.THREADS_PER_PAGE
            }),
            headers=ANY,
            timeout=ANY
        )
        return response

    def check_html(self, mock_request, **params):  # lint-amnesty, pylint: disable=missing-function-docstring
        response = self.get_response(mock_request, params)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/html; charset=utf-8'
        html = response.content.decode('utf-8')
        self.assertRegex(html, r'data-page="1"')
        self.assertRegex(html, r'data-num-pages="1"')
        self.assertRegex(html, r'<span class="discussion-count">1</span> discussion started')
        self.assertRegex(html, r'<span class="discussion-count">2</span> comments')
        self.assertRegex(html, f'&#39;id&#39;: &#39;{self.TEST_THREAD_ID}&#39;')
        self.assertRegex(html, f'&#39;title&#39;: &#39;{self.TEST_THREAD_TEXT}&#39;')
        self.assertRegex(html, f'&#39;body&#39;: &#39;{self.TEST_THREAD_TEXT}&#39;')
        self.assertRegex(html, f'&#39;username&#39;: &#39;{self.student.username}&#39;')

    def check_ajax(self, mock_request, **params):  # lint-amnesty, pylint: disable=missing-function-docstring
        response = self.get_response(mock_request, params, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json; charset=utf-8'
        response_data = json.loads(response.content.decode('utf-8'))
        assert sorted(response_data.keys()) == ['annotated_content_info', 'discussion_data', 'num_pages', 'page']
        assert len(response_data['discussion_data']) == 1
        assert response_data['page'] == 1
        assert response_data['num_pages'] == 1
        assert response_data['discussion_data'][0]['id'] == self.TEST_THREAD_ID
        assert response_data['discussion_data'][0]['title'] == self.TEST_THREAD_TEXT
        assert response_data['discussion_data'][0]['body'] == self.TEST_THREAD_TEXT

    def test_html(self, mock_request):
        self.check_html(mock_request)

    def test_ajax(self, mock_request):
        self.check_ajax(mock_request)

    def test_404_non_enrolled_user(self, __):
        """
        Test that when student try to visit un-enrolled students' discussion profile,
        the system raises Http404.
        """
        unenrolled_user = UserFactory.create()
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        with pytest.raises(Http404):
            views.user_profile(
                request,
                str(self.course.id),
                unenrolled_user.id
            )

    def test_404_profiled_user(self, _mock_request):
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        with pytest.raises(Http404):
            views.user_profile(
                request,
                str(self.course.id),
                -999
            )

    def test_404_course(self, _mock_request):
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        with pytest.raises(Http404):
            views.user_profile(
                request,
                "non/existent/course",
                self.profiled_user.id
            )

    def test_post(self, mock_request):
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text=self.TEST_THREAD_TEXT, thread_id=self.TEST_THREAD_ID
        )
        request = RequestFactory().post("dummy_url")
        request.user = self.student
        response = views.user_profile(
            request,
            str(self.course.id),
            self.profiled_user.id
        )
        assert response.status_code == 405


@patch('requests.request', autospec=True)
class CommentsServiceRequestHeadersTestCase(ForumsEnableMixin, UrlResetMixin, ModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    CREATE_USER = False

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()

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


class InlineDiscussionUnicodeTestCase(ForumsEnableMixin, SharedModuleStoreTestCase, UnicodeTestMixin):  # lint-amnesty, pylint: disable=missing-class-docstring

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

        response = views.inline_discussion(
            request, str(self.course.id), self.course.discussion_topics['General']['id']
        )
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data['discussion_data'][0]['title'] == text
        assert response_data['discussion_data'][0]['body'] == text


class ForumFormDiscussionUnicodeTestCase(ForumsEnableMixin, SharedModuleStoreTestCase, UnicodeTestMixin):  # lint-amnesty, pylint: disable=missing-class-docstring

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
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # so request.is_ajax() == True

        response = views.forum_form_discussion(request, str(self.course.id))
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data['discussion_data'][0]['title'] == text
        assert response_data['discussion_data'][0]['body'] == text


@ddt.ddt
@patch('openedx.core.djangoapps.django_comment_common.comment_client.utils.requests.request', autospec=True)
class ForumDiscussionXSSTestCase(ForumsEnableMixin, UrlResetMixin, ModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()

        username = "foo"
        password = "bar"

        self.course = CourseFactory.create()
        self.student = UserFactory.create(username=username, password=password)
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        assert self.client.login(username=username, password=password)

    @ddt.data('"><script>alert(1)</script>', '<script>alert(1)</script>', '</script><script>alert(1)</script>')
    @patch('common.djangoapps.student.models.cc.User.from_django_user')
    def test_forum_discussion_xss_prevent(self, malicious_code, mock_user, mock_req):
        """
        Test that XSS attack is prevented
        """
        mock_user.return_value.to_dict.return_value = {}
        mock_req.return_value.status_code = 200
        reverse_url = "{}{}".format(reverse(
            "forum_form_discussion",
            kwargs={"course_id": str(self.course.id)}), '/forum_form_discussion')
        # Test that malicious code does not appear in html
        url = "{}?{}={}".format(reverse_url, 'sort_key', malicious_code)
        resp = self.client.get(url)
        self.assertNotContains(resp, malicious_code)

    @ddt.data('"><script>alert(1)</script>', '<script>alert(1)</script>', '</script><script>alert(1)</script>')
    @patch('common.djangoapps.student.models.cc.User.from_django_user')
    @patch('common.djangoapps.student.models.cc.User.active_threads')
    def test_forum_user_profile_xss_prevent(self, malicious_code, mock_threads, mock_from_django_user, mock_request):
        """
        Test that XSS attack is prevented
        """
        mock_threads.return_value = [], 1, 1
        mock_from_django_user.return_value.to_dict.return_value = {
            'upvoted_ids': [],
            'downvoted_ids': [],
            'subscribed_thread_ids': []
        }
        mock_request.side_effect = make_mock_request_impl(course=self.course, text='dummy')

        url = reverse('user_profile',
                      kwargs={'course_id': str(self.course.id), 'user_id': str(self.student.id)})
        # Test that malicious code does not appear in html
        url_string = "{}?{}={}".format(url, 'page', malicious_code)
        resp = self.client.get(url_string)
        self.assertNotContains(resp, malicious_code)


class ForumDiscussionSearchUnicodeTestCase(ForumsEnableMixin, SharedModuleStoreTestCase, UnicodeTestMixin):  # lint-amnesty, pylint: disable=missing-class-docstring

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
        data = {
            "ajax": 1,
            "text": text,
        }
        request = RequestFactory().get("dummy_url", data)
        request.user = self.student
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # so request.is_ajax() == True

        response = views.forum_form_discussion(request, str(self.course.id))
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data['discussion_data'][0]['title'] == text
        assert response_data['discussion_data'][0]['body'] == text


class SingleThreadUnicodeTestCase(ForumsEnableMixin, SharedModuleStoreTestCase, UnicodeTestMixin):  # lint-amnesty, pylint: disable=missing-class-docstring

    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create(discussion_topics={'dummy_discussion_id': {'id': 'dummy_discussion_id'}})

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
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # so request.is_ajax() == True

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
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # so request.is_ajax() == True

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
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # so request.is_ajax() == True

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


@patch('requests.request', autospec=True)
class EnterpriseConsentTestCase(EnterpriseTestConsentRequired, ForumsEnableMixin, UrlResetMixin, ModuleStoreTestCase):
    """
    Ensure that the Enterprise Data Consent redirects are in place only when consent is required.
    """
    CREATE_USER = False

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        # Invoke UrlResetMixin setUp
        super().setUp()

        username = "foo"
        password = "bar"

        self.discussion_id = 'dummy_discussion_id'
        self.course = CourseFactory.create(discussion_topics={'dummy discussion': {'id': self.discussion_id}})
        self.student = UserFactory.create(username=username, password=password)
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        assert self.client.login(username=username, password=password)

        self.addCleanup(translation.deactivate)

    @patch('openedx.features.enterprise_support.api.enterprise_customer_for_request')
    def test_consent_required(self, mock_enterprise_customer_for_request, mock_request):
        """
        Test that enterprise data sharing consent is required when enabled for the various discussion views.
        """
        # ENT-924: Temporary solution to replace sensitive SSO usernames.
        mock_enterprise_customer_for_request.return_value = None

        thread_id = 'dummy'
        course_id = str(self.course.id)
        mock_request.side_effect = make_mock_request_impl(course=self.course, text='dummy', thread_id=thread_id)

        for url in (
                reverse('forum_form_discussion',
                        kwargs=dict(course_id=course_id)),
                reverse('single_thread',
                        kwargs=dict(course_id=course_id, discussion_id=self.discussion_id, thread_id=thread_id)),
        ):
            self.verify_consent_required(self.client, url)  # pylint: disable=no-value-for-parameter


class DividedDiscussionsTestCase(CohortViewsTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def create_divided_discussions(self):
        """
        Set up a divided discussion in the system, complete with all the fixings
        """
        divided_inline_discussions = ['Topic A']
        divided_course_wide_discussions = ["Topic B"]
        divided_discussions = divided_inline_discussions + divided_course_wide_discussions

        # inline discussion
        ItemFactory.create(
            parent_location=self.course.location,
            category="discussion",
            discussion_id=topic_name_to_id(self.course, "Topic A"),
            discussion_category="Chapter",
            discussion_target="Discussion",
            start=datetime.now()
        )
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
    MODULESTORE = TEST_DATA_MONGO_AMNESTY_MODULESTORE

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
    MODULESTORE = TEST_DATA_MONGO_AMNESTY_MODULESTORE

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
        ItemFactory.create(
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

        self.category = ItemFactory.create(
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
            self.client.login(username=self.user.username, password='test')
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
            self.client.login(username=self.user.username, password='test')
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
            self.client.login(username=self.user.username, password='test')
            url = reverse("single_thread", args=[self.course.id, "test_discussion", "test_thread"])
            response = self.client.get(url)
            assert response.status_code == 302
            expected_url = f"{settings.DISCUSSIONS_MICROFRONTEND_URL}/{str(self.course.id)}/posts/test_thread"
            assert response.url == expected_url

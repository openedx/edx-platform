import json
import logging

import ddt
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from edxmako.tests import mako_middleware_process_request

from django_comment_common.utils import ThreadContext
from django_comment_client.forum import views
from django_comment_client.permissions import get_team
from django_comment_client.tests.group_id import (
    CohortedTopicGroupIdTestMixin,
    NonCohortedTopicGroupIdTestMixin
)
from django_comment_client.tests.unicode import UnicodeTestMixin
from django_comment_client.tests.utils import CohortedTestCase
from django_comment_client.utils import strip_none
from student.models import UserProfile
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from util.testing import UrlResetMixin
from openedx.core.djangoapps.util.testing import ContentGroupTestCase
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    TEST_DATA_MONGO_MODULESTORE
)
from xmodule.modulestore.tests.factories import check_mongo_calls, CourseFactory, ItemFactory

from courseware.courses import UserNotEnrolled
from nose.tools import assert_true
from mock import patch, Mock, ANY, call

from openedx.core.djangoapps.course_groups.models import CourseUserGroup

from lms.djangoapps.teams.tests.factories import CourseTeamFactory

log = logging.getLogger(__name__)

# pylint: disable=missing-docstring


class ViewsExceptionTestCase(UrlResetMixin, ModuleStoreTestCase):

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):

        # Patching the ENABLE_DISCUSSION_SERVICE value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super(ViewsExceptionTestCase, self).setUp()

        # create a course
        self.course = CourseFactory.create(org='MITx', course='999',
                                           display_name='Robot Super Course')

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('student.models.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            password = 'test'

            # Create the student
            self.student = UserFactory(username=uname, password=password, email=email)

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

            # Log the student in
            self.client = Client()
            assert_true(self.client.login(username=uname, password=password))

    @patch('student.models.cc.User.from_django_user')
    @patch('student.models.cc.User.active_threads')
    def test_user_profile_exception(self, mock_threads, mock_from_django_user):

        # Mock the code that makes the HTTP requests to the cs_comment_service app
        # for the profiled user's active threads
        mock_threads.return_value = [], 1, 1

        # Mock the code that makes the HTTP request to the cs_comment_service app
        # that gets the current user's info
        mock_from_django_user.return_value = Mock()

        url = reverse('django_comment_client.forum.views.user_profile',
                      kwargs={'course_id': self.course.id.to_deprecated_string(), 'user_id': '12345'})  # There is no user 12345
        self.response = self.client.get(url)
        self.assertEqual(self.response.status_code, 404)

    @patch('student.models.cc.User.from_django_user')
    @patch('student.models.cc.User.subscribed_threads')
    def test_user_followed_threads_exception(self, mock_threads, mock_from_django_user):

        # Mock the code that makes the HTTP requests to the cs_comment_service app
        # for the profiled user's active threads
        mock_threads.return_value = [], 1, 1

        # Mock the code that makes the HTTP request to the cs_comment_service app
        # that gets the current user's info
        mock_from_django_user.return_value = Mock()

        url = reverse('django_comment_client.forum.views.followed_threads',
                      kwargs={'course_id': self.course.id.to_deprecated_string(), 'user_id': '12345'})  # There is no user 12345
        self.response = self.client.get(url)
        self.assertEqual(self.response.status_code, 404)


def make_mock_thread_data(
        course,
        text,
        thread_id,
        num_children,
        group_id=None,
        group_name=None,
        commentable_id=None,
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
        "context": (
            ThreadContext.COURSE if get_team(data_commentable_id) is None else ThreadContext.STANDALONE
        )
    }
    if group_id is not None:
        thread_data['group_name'] = group_name
    if num_children is not None:
        thread_data["children"] = [{
            "id": "dummy_comment_id_{}".format(i),
            "type": "comment",
            "body": text,
        } for i in range(num_children)]
    return thread_data


def make_mock_request_impl(
        course,
        text,
        thread_id="dummy_thread_id",
        group_id=None,
        commentable_id=None,
        num_thread_responses=1,
):
    def mock_request_impl(*args, **kwargs):
        url = args[1]
        data = None
        if url.endswith("threads") or url.endswith("user_profile"):
            data = {
                "collection": [
                    make_mock_thread_data(
                        course=course,
                        text=text,
                        thread_id=thread_id,
                        num_children=None,
                        group_id=group_id,
                        commentable_id=commentable_id,
                    )
                ]
            }
        elif thread_id and url.endswith(thread_id):
            data = make_mock_thread_data(
                course=course,
                text=text,
                thread_id=thread_id,
                num_children=num_thread_responses,
                group_id=group_id,
                commentable_id=commentable_id
            )
        elif "/users/" in url:
            data = {
                "default_sort_key": "date",
                "upvoted_ids": [],
                "downvoted_ids": [],
                "subscribed_thread_ids": [],
            }
            # comments service adds these attributes when course_id param is present
            if kwargs.get('params', {}).get('course_id'):
                data.update({
                    "threads_count": 1,
                    "comments_count": 2
                })
        if data:
            return Mock(status_code=200, text=json.dumps(data), json=Mock(return_value=data))
        return Mock(status_code=404)
    return mock_request_impl


class StringEndsWithMatcher(object):
    def __init__(self, suffix):
        self.suffix = suffix

    def __eq__(self, other):
        return other.endswith(self.suffix)


class PartialDictMatcher(object):
    def __init__(self, expected_values):
        self.expected_values = expected_values

    def __eq__(self, other):
        return all([
            key in other and other[key] == value
            for key, value in self.expected_values.iteritems()
        ])


@patch('requests.request', autospec=True)
class SingleThreadTestCase(ModuleStoreTestCase):
    def setUp(self):
        super(SingleThreadTestCase, self).setUp(create_user=False)

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
            self.course.id.to_deprecated_string(),
            "dummy_discussion_id",
            "test_thread_id"
        )

        self.assertEquals(response.status_code, 200)
        response_data = json.loads(response.content)
        # strip_none is being used to perform the same transform that the
        # django view performs prior to writing thread data to the response
        self.assertEquals(
            response_data["content"],
            strip_none(make_mock_thread_data(course=self.course, text=text, thread_id=thread_id, num_children=1))
        )
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
            self.course.id.to_deprecated_string(),
            "dummy_discussion_id",
            "test_thread_id"
        )
        self.assertEquals(response.status_code, 200)
        response_data = json.loads(response.content)
        # strip_none is being used to perform the same transform that the
        # django view performs prior to writing thread data to the response
        self.assertEquals(
            response_data["content"],
            strip_none(make_mock_thread_data(course=self.course, text=text, thread_id=thread_id, num_children=1))
        )
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

    def test_post(self, mock_request):
        request = RequestFactory().post("dummy_url")
        response = views.single_thread(
            request,
            self.course.id.to_deprecated_string(),
            "dummy_discussion_id",
            "dummy_thread_id"
        )
        self.assertEquals(response.status_code, 405)

    def test_not_found(self, mock_request):
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        # Mock request to return 404 for thread request
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy", thread_id=None)
        self.assertRaises(
            Http404,
            views.single_thread,
            request,
            self.course.id.to_deprecated_string(),
            "test_discussion_id",
            "test_thread_id"
        )


@ddt.ddt
@patch('requests.request', autospec=True)
class SingleThreadQueryCountTestCase(ModuleStoreTestCase):
    """
    Ensures the number of modulestore queries and number of sql queries are
    independent of the number of responses retrieved for a given discussion thread.
    """
    MODULESTORE = TEST_DATA_MONGO_MODULESTORE

    @ddt.data(
        # old mongo with cache
        (ModuleStoreEnum.Type.mongo, 1, 6, 4, 16, 8),
        (ModuleStoreEnum.Type.mongo, 50, 6, 4, 16, 8),
        # split mongo: 3 queries, regardless of thread response size.
        (ModuleStoreEnum.Type.split, 1, 3, 3, 16, 8),
        (ModuleStoreEnum.Type.split, 50, 3, 3, 16, 8),
    )
    @ddt.unpack
    def test_number_of_mongo_queries(
            self,
            default_store,
            num_thread_responses,
            num_uncached_mongo_calls,
            num_cached_mongo_calls,
            num_uncached_sql_queries,
            num_cached_sql_queries,
            mock_request
    ):
        with modulestore().default_store(default_store):
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
            response = views.single_thread(
                request,
                course.id.to_deprecated_string(),
                "dummy_discussion_id",
                test_thread_id
            )
            self.assertEquals(response.status_code, 200)
            self.assertEquals(len(json.loads(response.content)["content"]["children"]), num_thread_responses)

        # Test uncached first, then cached now that the cache is warm.
        cached_calls = [
            [num_uncached_mongo_calls, num_uncached_sql_queries],
            [num_cached_mongo_calls, num_cached_sql_queries],
        ]
        for expected_mongo_calls, expected_sql_queries in cached_calls:
            with self.assertNumQueries(expected_sql_queries):
                with check_mongo_calls(expected_mongo_calls):
                    call_single_thread()


@patch('requests.request', autospec=True)
class SingleCohortedThreadTestCase(CohortedTestCase):
    def _create_mock_cohorted_thread(self, mock_request):
        self.mock_text = "dummy content"
        self.mock_thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text=self.mock_text, thread_id=self.mock_thread_id, group_id=self.student_cohort.id
        )

    def test_ajax(self, mock_request):
        self._create_mock_cohorted_thread(mock_request)

        request = RequestFactory().get(
            "dummy_url",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        request.user = self.student
        response = views.single_thread(
            request,
            self.course.id.to_deprecated_string(),
            "cohorted_topic",
            self.mock_thread_id
        )

        self.assertEquals(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(
            response_data["content"],
            make_mock_thread_data(
                course=self.course,
                text=self.mock_text,
                thread_id=self.mock_thread_id,
                num_children=1,
                group_id=self.student_cohort.id,
                group_name=self.student_cohort.name
            )
        )

    def test_html(self, mock_request):
        self._create_mock_cohorted_thread(mock_request)

        request = RequestFactory().get("dummy_url")
        request.user = self.student
        mako_middleware_process_request(request)
        response = views.single_thread(
            request,
            self.course.id.to_deprecated_string(),
            "cohorted_topic",
            self.mock_thread_id
        )

        self.assertEquals(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        html = response.content

        # Verify that the group name is correctly included in the HTML
        self.assertRegexpMatches(html, r'&#34;group_name&#34;: &#34;student_cohort&#34;')


@patch('lms.lib.comment_client.utils.requests.request', autospec=True)
class SingleThreadAccessTestCase(CohortedTestCase):
    def call_view(self, mock_request, commentable_id, user, group_id, thread_group_id=None, pass_group_id=True):
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
            self.course.id.to_deprecated_string(),
            commentable_id,
            thread_id
        )

    def test_student_non_cohorted(self, mock_request):
        resp = self.call_view(mock_request, "non_cohorted_topic", self.student, self.student_cohort.id)
        self.assertEqual(resp.status_code, 200)

    def test_student_same_cohort(self, mock_request):
        resp = self.call_view(
            mock_request,
            "cohorted_topic",
            self.student,
            self.student_cohort.id,
            thread_group_id=self.student_cohort.id
        )
        self.assertEqual(resp.status_code, 200)

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
        self.assertEqual(resp.status_code, 200)

    def test_student_different_cohort(self, mock_request):
        self.assertRaises(
            Http404,
            lambda: self.call_view(
                mock_request,
                "cohorted_topic",
                self.student,
                self.student_cohort.id,
                thread_group_id=self.moderator_cohort.id
            )
        )

    def test_moderator_non_cohorted(self, mock_request):
        resp = self.call_view(mock_request, "non_cohorted_topic", self.moderator, self.moderator_cohort.id)
        self.assertEqual(resp.status_code, 200)

    def test_moderator_same_cohort(self, mock_request):
        resp = self.call_view(
            mock_request,
            "cohorted_topic",
            self.moderator,
            self.moderator_cohort.id,
            thread_group_id=self.moderator_cohort.id
        )
        self.assertEqual(resp.status_code, 200)

    def test_moderator_different_cohort(self, mock_request):
        resp = self.call_view(
            mock_request,
            "cohorted_topic",
            self.moderator,
            self.moderator_cohort.id,
            thread_group_id=self.student_cohort.id
        )
        self.assertEqual(resp.status_code, 200)


@patch('lms.lib.comment_client.utils.requests.request', autospec=True)
class SingleThreadGroupIdTestCase(CohortedTestCase, CohortedTopicGroupIdTestMixin):
    cs_endpoint = "/threads"

    def call_view(self, mock_request, commentable_id, user, group_id, pass_group_id=True, is_ajax=False):
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text="dummy context", group_id=self.student_cohort.id
        )

        request_data = {}
        if pass_group_id:
            request_data["group_id"] = group_id
        headers = {}
        if is_ajax:
            headers['HTTP_X_REQUESTED_WITH'] = "XMLHttpRequest"
        request = RequestFactory().get(
            "dummy_url",
            data=request_data,
            **headers
        )
        request.user = user
        mako_middleware_process_request(request)
        return views.single_thread(
            request,
            self.course.id.to_deprecated_string(),
            commentable_id,
            "dummy_thread_id"
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
class SingleThreadContentGroupTestCase(ContentGroupTestCase):
    def assert_can_access(self, user, discussion_id, thread_id, should_have_access):
        """
        Verify that a user has access to a thread within a given
        discussion_id when should_have_access is True, otherwise
        verify that the user does not have access to that thread.
        """
        request = RequestFactory().get("dummy_url")
        request.user = user
        mako_middleware_process_request(request)

        def call_single_thread():
            return views.single_thread(
                request,
                unicode(self.course.id),
                discussion_id,
                thread_id
            )

        if should_have_access:
            self.assertEqual(call_single_thread().status_code, 200)
        else:
            with self.assertRaises(Http404):
                call_single_thread()

    def test_staff_user(self, mock_request):
        """
        Verify that the staff user can access threads in the alpha,
        beta, and global discussion modules.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy content", thread_id=thread_id)

        for discussion_module in [self.alpha_module, self.beta_module, self.global_module]:
            self.assert_can_access(self.staff_user, discussion_module.discussion_id, thread_id, True)

    def test_alpha_user(self, mock_request):
        """
        Verify that the alpha user can access threads in the alpha and
        global discussion modules.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy content", thread_id=thread_id)

        for discussion_module in [self.alpha_module, self.global_module]:
            self.assert_can_access(self.alpha_user, discussion_module.discussion_id, thread_id, True)

        self.assert_can_access(self.alpha_user, self.beta_module.discussion_id, thread_id, False)

    def test_beta_user(self, mock_request):
        """
        Verify that the beta user can access threads in the beta and
        global discussion modules.
        """
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text="dummy content", thread_id=thread_id)

        for discussion_module in [self.beta_module, self.global_module]:
            self.assert_can_access(self.beta_user, discussion_module.discussion_id, thread_id, True)

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


@patch('lms.lib.comment_client.utils.requests.request', autospec=True)
class InlineDiscussionContextTestCase(ModuleStoreTestCase):
    def setUp(self):
        super(InlineDiscussionContextTestCase, self).setUp()
        self.course = CourseFactory.create()
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id)
        self.discussion_topic_id = "dummy_topic"
        self.team = CourseTeamFactory(
            name="A team",
            course_id=self.course.id,
            topic_id='topic_id',
            discussion_topic_id=self.discussion_topic_id
        )

        self.team.add_user(self.user)  # pylint: disable=no-member

        # Create the user a UserProfile so it doesn't act as a direct access user
        UserProfile(user=self.user).save()

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
            unicode(self.course.id),
            self.discussion_topic_id,
        )

        json_response = json.loads(response.content)
        self.assertEqual(json_response['discussion_data'][0]['context'], ThreadContext.STANDALONE)


@patch('lms.lib.comment_client.utils.requests.request', autospec=True)
class InlineDiscussionGroupIdTestCase(
        CohortedTestCase,
        CohortedTopicGroupIdTestMixin,
        NonCohortedTopicGroupIdTestMixin
):
    cs_endpoint = "/threads"

    def setUp(self):
        super(InlineDiscussionGroupIdTestCase, self).setUp()
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
            self.course.id.to_deprecated_string(),
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


@patch('lms.lib.comment_client.utils.requests.request', autospec=True)
class ForumFormDiscussionGroupIdTestCase(CohortedTestCase, CohortedTopicGroupIdTestMixin):
    cs_endpoint = "/threads"

    def call_view(self, mock_request, commentable_id, user, group_id, pass_group_id=True, is_ajax=False):
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
        request = RequestFactory().get(
            "dummy_url",
            data=request_data,
            **headers
        )
        request.user = user
        mako_middleware_process_request(request)
        return views.forum_form_discussion(
            request,
            self.course.id.to_deprecated_string()
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


@patch('lms.lib.comment_client.utils.requests.request', autospec=True)
class UserProfileDiscussionGroupIdTestCase(CohortedTestCase, CohortedTopicGroupIdTestMixin):
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
        request = RequestFactory().get(
            "dummy_url",
            data=request_data,
            **headers
        )
        request.user = requesting_user
        mako_middleware_process_request(request)
        return views.user_profile(
            request,
            self.course.id.to_deprecated_string(),
            profiled_user.id
        )

    def call_view(self, mock_request, _commentable_id, user, group_id, pass_group_id=True, is_ajax=False):
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
            self.assertTrue(
                False,
                "Did not find appropriate user_profile call for 'for_specific_course'=" + for_specific_course
            )

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
        self.assertNotIn("group_id", params_without_course_id)

        params_with_course_id = get_params_from_user_info_call(True)
        if expect_group_id_in_request:
            self.assertIn("group_id", params_with_course_id)
            self.assertEqual(group_id, params_with_course_id["group_id"])
        else:
            self.assertNotIn("group_id", params_with_course_id)

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


@patch('lms.lib.comment_client.utils.requests.request', autospec=True)
class FollowedThreadsDiscussionGroupIdTestCase(CohortedTestCase, CohortedTopicGroupIdTestMixin):
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
            self.course.id.to_deprecated_string(),
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


@patch('lms.lib.comment_client.utils.requests.request', autospec=True)
class InlineDiscussionTestCase(ModuleStoreTestCase):
    def setUp(self):
        super(InlineDiscussionTestCase, self).setUp()

        self.course = CourseFactory.create(org="TestX", number="101", display_name="Test Course")
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
            request, self.course.id.to_deprecated_string(), self.discussion1.discussion_id
        )

    def verify_response(self, response):
        """Verifies that the response contains the appropriate courseware_url and courseware_title"""
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected_courseware_url = '/courses/TestX/101/Test_Course/jump_to/i4x://TestX/101/discussion/Discussion1'
        expected_courseware_title = 'Chapter / Discussion1'
        self.assertEqual(response_data['discussion_data'][0]['courseware_url'], expected_courseware_url)
        self.assertEqual(response_data["discussion_data"][0]["courseware_title"], expected_courseware_title)

    def test_courseware_data(self, mock_request):
        self.verify_response(self.send_request(mock_request))

    def test_context(self, mock_request):
        team = CourseTeamFactory(
            name='Team Name',
            topic_id='A topic',
            course_id=self.course.id,
            discussion_topic_id=self.discussion1.discussion_id
        )

        team.add_user(self.student)  # pylint: disable=no-member

        response = self.send_request(mock_request)
        self.assertEqual(mock_request.call_args[1]['params']['context'], ThreadContext.STANDALONE)
        self.verify_response(response)


@patch('requests.request', autospec=True)
class UserProfileTestCase(ModuleStoreTestCase):

    TEST_THREAD_TEXT = 'userprofile-test-text'
    TEST_THREAD_ID = 'userprofile-test-thread-id'

    def setUp(self):
        super(UserProfileTestCase, self).setUp()

        self.course = CourseFactory.create()
        self.student = UserFactory.create()
        self.profiled_user = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)

    def get_response(self, mock_request, params, **headers):
        mock_request.side_effect = make_mock_request_impl(
            course=self.course, text=self.TEST_THREAD_TEXT, thread_id=self.TEST_THREAD_ID
        )
        request = RequestFactory().get("dummy_url", data=params, **headers)
        request.user = self.student

        mako_middleware_process_request(request)
        response = views.user_profile(
            request,
            self.course.id.to_deprecated_string(),
            self.profiled_user.id
        )
        mock_request.assert_any_call(
            "get",
            StringEndsWithMatcher('/users/{}/active_threads'.format(self.profiled_user.id)),
            data=None,
            params=PartialDictMatcher({
                "course_id": self.course.id.to_deprecated_string(),
                "page": params.get("page", 1),
                "per_page": views.THREADS_PER_PAGE
            }),
            headers=ANY,
            timeout=ANY
        )
        return response

    def check_html(self, mock_request, **params):
        response = self.get_response(mock_request, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        html = response.content
        self.assertRegexpMatches(html, r'data-page="1"')
        self.assertRegexpMatches(html, r'data-num-pages="1"')
        self.assertRegexpMatches(html, r'<span>1</span> discussion started')
        self.assertRegexpMatches(html, r'<span>2</span> comments')
        self.assertRegexpMatches(html, r'&#34;id&#34;: &#34;{}&#34;'.format(self.TEST_THREAD_ID))
        self.assertRegexpMatches(html, r'&#34;title&#34;: &#34;{}&#34;'.format(self.TEST_THREAD_TEXT))
        self.assertRegexpMatches(html, r'&#34;body&#34;: &#34;{}&#34;'.format(self.TEST_THREAD_TEXT))
        self.assertRegexpMatches(html, r'&#34;username&#34;: &#34;{}&#34;'.format(self.student.username))

    def check_ajax(self, mock_request, **params):
        response = self.get_response(mock_request, params, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        response_data = json.loads(response.content)
        self.assertEqual(
            sorted(response_data.keys()),
            ["annotated_content_info", "discussion_data", "num_pages", "page"]
        )
        self.assertEqual(len(response_data['discussion_data']), 1)
        self.assertEqual(response_data["page"], 1)
        self.assertEqual(response_data["num_pages"], 1)
        self.assertEqual(response_data['discussion_data'][0]['id'], self.TEST_THREAD_ID)
        self.assertEqual(response_data['discussion_data'][0]['title'], self.TEST_THREAD_TEXT)
        self.assertEqual(response_data['discussion_data'][0]['body'], self.TEST_THREAD_TEXT)

    def test_html(self, mock_request):
        self.check_html(mock_request)

    def test_html_p2(self, mock_request):
        self.check_html(mock_request, page="2")

    def test_ajax(self, mock_request):
        self.check_ajax(mock_request)

    def test_ajax_p2(self, mock_request):
        self.check_ajax(mock_request, page="2")

    def test_404_profiled_user(self, mock_request):
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        with self.assertRaises(Http404):
            views.user_profile(
                request,
                self.course.id.to_deprecated_string(),
                -999
            )

    def test_404_course(self, mock_request):
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        with self.assertRaises(Http404):
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
            self.course.id.to_deprecated_string(),
            self.profiled_user.id
        )
        self.assertEqual(response.status_code, 405)


@patch('requests.request', autospec=True)
class CommentsServiceRequestHeadersTestCase(UrlResetMixin, ModuleStoreTestCase):
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(CommentsServiceRequestHeadersTestCase, self).setUp()

        username = "foo"
        password = "bar"

        # Invoke UrlResetMixin
        super(CommentsServiceRequestHeadersTestCase, self).setUp(create_user=False)
        self.course = CourseFactory.create(discussion_topics={'dummy discussion': {'id': 'dummy_discussion_id'}})
        self.student = UserFactory.create(username=username, password=password)
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        self.assertTrue(
            self.client.login(username=username, password=password)
        )

    def assert_all_calls_have_header(self, mock_request, key, value):
        expected = call(
            ANY,  # method
            ANY,  # url
            data=ANY,
            params=ANY,
            headers=PartialDictMatcher({key: value}),
            timeout=ANY
        )
        for actual in mock_request.call_args_list:
            self.assertEqual(expected, actual)

    def test_accept_language(self, mock_request):
        lang = "eo"
        text = "dummy content"
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text, thread_id=thread_id)

        self.client.get(
            reverse(
                "django_comment_client.forum.views.single_thread",
                kwargs={
                    "course_id": self.course.id.to_deprecated_string(),
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
                "django_comment_client.forum.views.forum_form_discussion",
                kwargs={"course_id": self.course.id.to_deprecated_string()}
            ),
        )
        self.assert_all_calls_have_header(mock_request, "X-Edx-Api-Key", "test_api_key")


class InlineDiscussionUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin):
    def setUp(self):
        super(InlineDiscussionUnicodeTestCase, self).setUp()

        self.course = CourseFactory.create()
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text)
        request = RequestFactory().get("dummy_url")
        request.user = self.student

        response = views.inline_discussion(
            request, self.course.id.to_deprecated_string(), self.course.discussion_topics['General']['id']
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["discussion_data"][0]["title"], text)
        self.assertEqual(response_data["discussion_data"][0]["body"], text)


class ForumFormDiscussionUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin):
    def setUp(self):
        super(ForumFormDiscussionUnicodeTestCase, self).setUp()

        self.course = CourseFactory.create()
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text)
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # so request.is_ajax() == True

        response = views.forum_form_discussion(request, self.course.id.to_deprecated_string())
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["discussion_data"][0]["title"], text)
        self.assertEqual(response_data["discussion_data"][0]["body"], text)


@ddt.ddt
@patch('lms.lib.comment_client.utils.requests.request', autospec=True)
class ForumDiscussionXSSTestCase(UrlResetMixin, ModuleStoreTestCase):
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(ForumDiscussionXSSTestCase, self).setUp()

        username = "foo"
        password = "bar"

        self.course = CourseFactory.create()
        self.student = UserFactory.create(username=username, password=password)
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        self.assertTrue(self.client.login(username=username, password=password))

    @ddt.data('"><script>alert(1)</script>', '<script>alert(1)</script>', '</script><script>alert(1)</script>')
    @patch('student.models.cc.User.from_django_user')
    def test_forum_discussion_xss_prevent(self, malicious_code, mock_user, mock_req):  # pylint: disable=unused-argument
        """
        Test that XSS attack is prevented
        """
        reverse_url = "%s%s" % (reverse(
            "django_comment_client.forum.views.forum_form_discussion",
            kwargs={"course_id": unicode(self.course.id)}), '/forum_form_discussion')
        # Test that malicious code does not appear in html
        url = "%s?%s=%s" % (reverse_url, 'sort_key', malicious_code)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(malicious_code, resp.content)

    @ddt.data('"><script>alert(1)</script>', '<script>alert(1)</script>', '</script><script>alert(1)</script>')
    @patch('student.models.cc.User.from_django_user')
    @patch('student.models.cc.User.active_threads')
    def test_forum_user_profile_xss_prevent(self, malicious_code, mock_threads, mock_from_django_user, mock_request):
        """
        Test that XSS attack is prevented
        """
        mock_threads.return_value = [], 1, 1
        mock_from_django_user.return_value = Mock()
        mock_request.side_effect = make_mock_request_impl(course=self.course, text='dummy')

        url = reverse('django_comment_client.forum.views.user_profile',
                      kwargs={'course_id': unicode(self.course.id), 'user_id': str(self.student.id)})
        # Test that malicious code does not appear in html
        url_string = "%s?%s=%s" % (url, 'page', malicious_code)
        resp = self.client.get(url_string)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(malicious_code, resp.content)


class ForumDiscussionSearchUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin):
    def setUp(self):
        super(ForumDiscussionSearchUnicodeTestCase, self).setUp()

        self.course = CourseFactory.create()
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text)
        data = {
            "ajax": 1,
            "text": text,
        }
        request = RequestFactory().get("dummy_url", data)
        request.user = self.student
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # so request.is_ajax() == True

        response = views.forum_form_discussion(request, self.course.id.to_deprecated_string())
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["discussion_data"][0]["title"], text)
        self.assertEqual(response_data["discussion_data"][0]["body"], text)


class SingleThreadUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin):
    def setUp(self):
        super(SingleThreadUnicodeTestCase, self).setUp()

        self.course = CourseFactory.create(discussion_topics={'dummy_discussion_id': {'id': 'dummy_discussion_id'}})
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):
        thread_id = "test_thread_id"
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text, thread_id=thread_id)
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # so request.is_ajax() == True

        response = views.single_thread(request, self.course.id.to_deprecated_string(), "dummy_discussion_id", thread_id)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["content"]["title"], text)
        self.assertEqual(response_data["content"]["body"], text)


class UserProfileUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin):
    def setUp(self):
        super(UserProfileUnicodeTestCase, self).setUp()

        self.course = CourseFactory.create()
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text)
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # so request.is_ajax() == True

        response = views.user_profile(request, self.course.id.to_deprecated_string(), str(self.student.id))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["discussion_data"][0]["title"], text)
        self.assertEqual(response_data["discussion_data"][0]["body"], text)


class FollowedThreadsUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin):
    def setUp(self):
        super(FollowedThreadsUnicodeTestCase, self).setUp()

        self.course = CourseFactory.create()
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request', autospec=True)
    def _test_unicode_data(self, text, mock_request):
        mock_request.side_effect = make_mock_request_impl(course=self.course, text=text)
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # so request.is_ajax() == True

        response = views.followed_threads(request, self.course.id.to_deprecated_string(), str(self.student.id))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["discussion_data"][0]["title"], text)
        self.assertEqual(response_data["discussion_data"][0]["body"], text)


class EnrollmentTestCase(ModuleStoreTestCase):
    """
    Tests for the behavior of views depending on if the student is enrolled
    in the course
    """

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(EnrollmentTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.student = UserFactory.create()

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    @patch('lms.lib.comment_client.utils.requests.request', autospec=True)
    def test_unenrolled(self, mock_request):
        mock_request.side_effect = make_mock_request_impl(course=self.course, text='dummy')
        request = RequestFactory().get('dummy_url')
        request.user = self.student
        with self.assertRaises(UserNotEnrolled):
            views.forum_form_discussion(request, course_id=self.course.id.to_deprecated_string())

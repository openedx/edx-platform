"""Tests for django comment client views."""
from contextlib import contextmanager
import logging
import json
import ddt

from django.conf import settings
from django.core.cache import get_cache
from django.test.client import Client, RequestFactory
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.urlresolvers import reverse
from request_cache.middleware import RequestCache
from mock import patch, ANY, Mock
from nose.tools import assert_true, assert_equal  # pylint: disable=no-name-in-module
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from lms.lib.comment_client import Thread

from common.test.utils import MockSignalHandlerMixin, disable_signal
from django_comment_client.base import views
from django_comment_client.tests.group_id import CohortedTopicGroupIdTestMixin, NonCohortedTopicGroupIdTestMixin, GroupIdAssertionMixin
from django_comment_client.tests.utils import CohortedTestCase
from django_comment_client.tests.unicode import UnicodeTestMixin
from django_comment_common.models import Role
from django_comment_common.utils import seed_permissions_roles, ThreadContext
from student.tests.factories import CourseEnrollmentFactory, UserFactory, CourseAccessRoleFactory
from teams.tests.factories import CourseTeamFactory, CourseTeamMembershipFactory
from util.testing import UrlResetMixin
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import check_mongo_calls
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum


log = logging.getLogger(__name__)

CS_PREFIX = "http://localhost:4567/api/v1"

# pylint: disable=missing-docstring


class MockRequestSetupMixin(object):
    def _create_response_mock(self, data):
        return Mock(text=json.dumps(data), json=Mock(return_value=data))

    def _set_mock_request_data(self, mock_request, data):
        mock_request.return_value = self._create_response_mock(data)


@patch('lms.lib.comment_client.utils.requests.request')
class CreateThreadGroupIdTestCase(
        MockRequestSetupMixin,
        CohortedTestCase,
        CohortedTopicGroupIdTestMixin,
        NonCohortedTopicGroupIdTestMixin
):
    cs_endpoint = "/threads"

    def call_view(self, mock_request, commentable_id, user, group_id, pass_group_id=True):
        self._set_mock_request_data(mock_request, {})
        mock_request.return_value.status_code = 200
        request_data = {"body": "body", "title": "title", "thread_type": "discussion"}
        if pass_group_id:
            request_data["group_id"] = group_id
        request = RequestFactory().post("dummy_url", request_data)
        request.user = user
        request.view_name = "create_thread"

        return views.create_thread(
            request,
            course_id=unicode(self.course.id),
            commentable_id=commentable_id
        )

    def test_group_info_in_response(self, mock_request):
        response = self.call_view(
            mock_request,
            "cohorted_topic",
            self.student,
            None
        )
        self._assert_json_response_contains_group_info(response)


@patch('lms.lib.comment_client.utils.requests.request')
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
                "commentable_id": "non_team_dummy_id"
            }
        )
        mock_request.return_value.status_code = 200
        request = RequestFactory().post("dummy_url", post_params or {})
        request.user = user or self.student
        request.view_name = view_name

        return getattr(views, view_name)(
            request,
            course_id=unicode(self.course.id),
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


class ViewsTestCaseMixin(object):
    """
    This class is used by both ViewsQueryCountTestCase and ViewsTestCase. By
    breaking out set_up_course into its own method, ViewsQueryCountTestCase
    can build a course in a particular modulestore, while ViewsTestCase can
    just run it in setUp for all tests.
    """

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
                discussion_id='id_module_{}'.format(i),
                discussion_category='Category {}'.format(i),
                discussion_target='Discussion {}'.format(i)
            )

        # seed the forums permissions and roles
        call_command('seed_permissions_roles', unicode(self.course_id))

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('student.models.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            self.password = 'test'  # pylint: disable=attribute-defined-outside-init

            # Create the user and make them active so we can log them in.
            self.student = User.objects.create_user(uname, email, self.password)  # pylint: disable=attribute-defined-outside-init
            self.student.is_active = True
            self.student.save()

            # Add a discussion moderator
            self.moderator = UserFactory.create(password=self.password)  # pylint: disable=attribute-defined-outside-init

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student,
                                    course_id=self.course_id)

            # Enroll the moderator and give them the appropriate roles
            CourseEnrollmentFactory(user=self.moderator, course_id=self.course.id)
            self.moderator.roles.add(Role.objects.get(name="Moderator", course_id=self.course.id))

            self.client = Client()
            assert_true(self.client.login(username='student', password=self.password))

    def _setup_mock_request(self, mock_request, include_depth=False):
        """
        Ensure that mock_request returns the data necessary to make views
        function correctly
        """
        mock_request.return_value.status_code = 200
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
        mock_request.return_value.status_code = 200
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
                                               'course_id': unicode(self.course_id)})
        response = self.client.post(url, data=thread)
        assert_true(mock_request.called)
        expected_data = {
            'thread_type': 'discussion',
            'body': u'this is a post',
            'context': ThreadContext.COURSE,
            'anonymous_to_peers': False, 'user_id': 1,
            'title': u'Hello',
            'commentable_id': u'i4x-MITx-999-course-Robot_Super_Course',
            'anonymous': False,
            'course_id': unicode(self.course_id),
        }
        if extra_response_data:
            expected_data.update(extra_response_data)
        mock_request.assert_called_with(
            'post',
            '{prefix}/i4x-MITx-999-course-Robot_Super_Course/threads'.format(prefix=CS_PREFIX),
            data=expected_data,
            params={'request_id': ANY},
            headers=ANY,
            timeout=5
        )
        assert_equal(response.status_code, 200)

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
                    "course_id": unicode(self.course_id)
                }),
                data={"body": "foo", "title": "foo", "commentable_id": "some_topic"}
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['body'], 'foo')
        self.assertEqual(data['title'], 'foo')
        self.assertEqual(data['commentable_id'], 'some_topic')


@ddt.ddt
@patch('lms.lib.comment_client.utils.requests.request')
@disable_signal(views, 'thread_created')
@disable_signal(views, 'thread_edited')
class ViewsQueryCountTestCase(UrlResetMixin, ModuleStoreTestCase, MockRequestSetupMixin, ViewsTestCaseMixin):

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(ViewsQueryCountTestCase, self).setUp(create_user=False)

    def clear_caches(self):
        """Clears caches so that query count numbers are accurate."""
        for cache in settings.CACHES:
            get_cache(cache).clear()
        RequestCache.clear_request_cache()

    def count_queries(func):  # pylint: disable=no-self-argument
        """
        Decorates test methods to count mongo and SQL calls for a
        particular modulestore.
        """
        def inner(self, default_store, module_count, mongo_calls, sql_queries, *args, **kwargs):
            with modulestore().default_store(default_store):
                self.set_up_course(module_count=module_count)
                self.clear_caches()
                with self.assertNumQueries(sql_queries):
                    with check_mongo_calls(mongo_calls):
                        func(self, *args, **kwargs)
        return inner

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 3, 4, 22),
        (ModuleStoreEnum.Type.mongo, 20, 4, 22),
        (ModuleStoreEnum.Type.split, 3, 13, 22),
        (ModuleStoreEnum.Type.split, 20, 13, 22),
    )
    @ddt.unpack
    @count_queries
    def test_create_thread(self, mock_request):
        self.create_thread_helper(mock_request)

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 3, 3, 16),
        (ModuleStoreEnum.Type.mongo, 20, 3, 16),
        (ModuleStoreEnum.Type.split, 3, 10, 16),
        (ModuleStoreEnum.Type.split, 20, 10, 16),
    )
    @ddt.unpack
    @count_queries
    def test_update_thread(self, mock_request):
        self.update_thread_helper(mock_request)


@ddt.ddt
@patch('lms.lib.comment_client.utils.requests.request')
class ViewsTestCase(
        UrlResetMixin,
        ModuleStoreTestCase,
        MockRequestSetupMixin,
        ViewsTestCaseMixin,
        MockSignalHandlerMixin
):

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        # Patching the ENABLE_DISCUSSION_SERVICE value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super(ViewsTestCase, self).setUp(create_user=False)
        self.set_up_course()

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

    def test_delete_thread(self, mock_request):
        self._set_mock_request_data(mock_request, {
            "user_id": str(self.student.id),
            "closed": False,
        })
        test_thread_id = "test_thread_id"
        request = RequestFactory().post("dummy_url", {"id": test_thread_id})
        request.user = self.student
        request.view_name = "delete_thread"
        with self.assert_discussion_signals('thread_deleted'):
            response = views.delete_thread(
                request,
                course_id=unicode(self.course.id),
                thread_id=test_thread_id
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_request.called)

    def test_delete_comment(self, mock_request):
        self._set_mock_request_data(mock_request, {
            "user_id": str(self.student.id),
            "closed": False,
        })
        test_comment_id = "test_comment_id"
        request = RequestFactory().post("dummy_url", {"id": test_comment_id})
        request.user = self.student
        request.view_name = "delete_comment"
        with self.assert_discussion_signals('comment_deleted'):
            response = views.delete_comment(
                request,
                course_id=unicode(self.course.id),
                comment_id=test_comment_id
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_request.called)
        args = mock_request.call_args[0]
        self.assertEqual(args[0], "delete")
        self.assertTrue(args[1].endswith("/{}".format(test_comment_id)))

    def _test_request_error(self, view_name, view_kwargs, data, mock_request):
        """
        Submit a request against the given view with the given data and ensure
        that the result is a 400 error and that no data was posted using
        mock_request
        """
        self._setup_mock_request(mock_request, include_depth=(view_name == "create_sub_comment"))

        response = self.client.post(reverse(view_name, kwargs=view_kwargs), data=data)
        self.assertEqual(response.status_code, 400)
        for call in mock_request.call_args_list:
            self.assertEqual(call[0][0].lower(), "get")

    def test_create_thread_no_title(self, mock_request):
        self._test_request_error(
            "create_thread",
            {"commentable_id": "dummy", "course_id": unicode(self.course_id)},
            {"body": "foo"},
            mock_request
        )

    def test_create_thread_empty_title(self, mock_request):
        self._test_request_error(
            "create_thread",
            {"commentable_id": "dummy", "course_id": unicode(self.course_id)},
            {"body": "foo", "title": " "},
            mock_request
        )

    def test_create_thread_no_body(self, mock_request):
        self._test_request_error(
            "create_thread",
            {"commentable_id": "dummy", "course_id": unicode(self.course_id)},
            {"title": "foo"},
            mock_request
        )

    def test_create_thread_empty_body(self, mock_request):
        self._test_request_error(
            "create_thread",
            {"commentable_id": "dummy", "course_id": unicode(self.course_id)},
            {"body": " ", "title": "foo"},
            mock_request
        )

    def test_update_thread_no_title(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": unicode(self.course_id)},
            {"body": "foo"},
            mock_request
        )

    def test_update_thread_empty_title(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": unicode(self.course_id)},
            {"body": "foo", "title": " "},
            mock_request
        )

    def test_update_thread_no_body(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": unicode(self.course_id)},
            {"title": "foo"},
            mock_request
        )

    def test_update_thread_empty_body(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": unicode(self.course_id)},
            {"body": " ", "title": "foo"},
            mock_request
        )

    def test_update_thread_course_topic(self, mock_request):
        with self.assert_discussion_signals('thread_edited'):
            self.update_thread_helper(mock_request)

    @patch('django_comment_client.utils.get_discussion_categories_ids', return_value=["test_commentable"])
    def test_update_thread_wrong_commentable_id(self, mock_get_discussion_id_map, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": unicode(self.course_id)},
            {"body": "foo", "title": "foo", "commentable_id": "wrong_commentable"},
            mock_request
        )

    def test_create_comment(self, mock_request):
        self._setup_mock_request(mock_request)
        with self.assert_discussion_signals('comment_created'):
            response = self.client.post(
                reverse(
                    "create_comment",
                    kwargs={"course_id": unicode(self.course_id), "thread_id": "dummy"}
                ),
                data={"body": "body"}
            )
        self.assertEqual(response.status_code, 200)

    def test_create_comment_no_body(self, mock_request):
        self._test_request_error(
            "create_comment",
            {"thread_id": "dummy", "course_id": unicode(self.course_id)},
            {},
            mock_request
        )

    def test_create_comment_empty_body(self, mock_request):
        self._test_request_error(
            "create_comment",
            {"thread_id": "dummy", "course_id": unicode(self.course_id)},
            {"body": " "},
            mock_request
        )

    def test_create_sub_comment_no_body(self, mock_request):
        self._test_request_error(
            "create_sub_comment",
            {"comment_id": "dummy", "course_id": unicode(self.course_id)},
            {},
            mock_request
        )

    def test_create_sub_comment_empty_body(self, mock_request):
        self._test_request_error(
            "create_sub_comment",
            {"comment_id": "dummy", "course_id": unicode(self.course_id)},
            {"body": " "},
            mock_request
        )

    def test_update_comment_no_body(self, mock_request):
        self._test_request_error(
            "update_comment",
            {"comment_id": "dummy", "course_id": unicode(self.course_id)},
            {},
            mock_request
        )

    def test_update_comment_empty_body(self, mock_request):
        self._test_request_error(
            "update_comment",
            {"comment_id": "dummy", "course_id": unicode(self.course_id)},
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
                    kwargs={"course_id": unicode(self.course_id), "comment_id": comment_id}
                ),
                data={"body": updated_body}
            )
        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_with(
            "put",
            "{prefix}/comments/{comment_id}".format(prefix=CS_PREFIX, comment_id=comment_id),
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
        mock_request.return_value.status_code = 200
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
            'course_id': unicode(self.course_id)
        })
        response = self.client.post(url)
        assert_true(mock_request.called)

        call_list = [
            (
                ('get', '{prefix}/threads/518d4237b023791dca00000d'.format(prefix=CS_PREFIX)),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('put', '{prefix}/threads/518d4237b023791dca00000d/abuse_flag'.format(prefix=CS_PREFIX)),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('get', '{prefix}/threads/518d4237b023791dca00000d'.format(prefix=CS_PREFIX)),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            )
        ]

        assert_equal(call_list, mock_request.call_args_list)

        assert_equal(response.status_code, 200)

    def test_un_flag_thread_open(self, mock_request):
        self.un_flag_thread(mock_request, False)

    def test_un_flag_thread_close(self, mock_request):
        self.un_flag_thread(mock_request, True)

    def un_flag_thread(self, mock_request, is_closed):
        mock_request.return_value.status_code = 200
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
            'course_id': unicode(self.course_id)
        })
        response = self.client.post(url)
        assert_true(mock_request.called)

        call_list = [
            (
                ('get', '{prefix}/threads/518d4237b023791dca00000d'.format(prefix=CS_PREFIX)),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('put', '{prefix}/threads/518d4237b023791dca00000d/abuse_unflag'.format(prefix=CS_PREFIX)),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('get', '{prefix}/threads/518d4237b023791dca00000d'.format(prefix=CS_PREFIX)),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            )
        ]

        assert_equal(call_list, mock_request.call_args_list)

        assert_equal(response.status_code, 200)

    def test_flag_comment_open(self, mock_request):
        self.flag_comment(mock_request, False)

    def test_flag_comment_close(self, mock_request):
        self.flag_comment(mock_request, True)

    def flag_comment(self, mock_request, is_closed):
        mock_request.return_value.status_code = 200
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
            'course_id': unicode(self.course_id)
        })
        response = self.client.post(url)
        assert_true(mock_request.called)

        call_list = [
            (
                ('get', '{prefix}/comments/518d4237b023791dca00000d'.format(prefix=CS_PREFIX)),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('put', '{prefix}/comments/518d4237b023791dca00000d/abuse_flag'.format(prefix=CS_PREFIX)),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('get', '{prefix}/comments/518d4237b023791dca00000d'.format(prefix=CS_PREFIX)),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            )
        ]

        assert_equal(call_list, mock_request.call_args_list)

        assert_equal(response.status_code, 200)

    def test_un_flag_comment_open(self, mock_request):
        self.un_flag_comment(mock_request, False)

    def test_un_flag_comment_close(self, mock_request):
        self.un_flag_comment(mock_request, True)

    def un_flag_comment(self, mock_request, is_closed):
        mock_request.return_value.status_code = 200
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
            'course_id': unicode(self.course_id)
        })
        response = self.client.post(url)
        assert_true(mock_request.called)

        call_list = [
            (
                ('get', '{prefix}/comments/518d4237b023791dca00000d'.format(prefix=CS_PREFIX)),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('put', '{prefix}/comments/518d4237b023791dca00000d/abuse_unflag'.format(prefix=CS_PREFIX)),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            ),
            (
                ('get', '{prefix}/comments/518d4237b023791dca00000d'.format(prefix=CS_PREFIX)),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': ANY,
                    'timeout': 5
                }
            )
        ]

        assert_equal(call_list, mock_request.call_args_list)

        assert_equal(response.status_code, 200)

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
                    kwargs={item_id: 'dummy', 'course_id': unicode(self.course_id)}
                )
            )
        self.assertEqual(response.status_code, 200)

    def test_endorse_comment(self, mock_request):
        self._setup_mock_request(mock_request)
        self.client.login(username=self.moderator.username, password=self.password)
        with self.assert_discussion_signals('comment_endorsed', user=self.moderator):
            response = self.client.post(
                reverse(
                    'endorse_comment',
                    kwargs={'comment_id': 'dummy', 'course_id': unicode(self.course_id)}
                )
            )
        self.assertEqual(response.status_code, 200)


@patch("lms.lib.comment_client.utils.requests.request")
@disable_signal(views, 'comment_endorsed')
class ViewPermissionsTestCase(UrlResetMixin, ModuleStoreTestCase, MockRequestSetupMixin):
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(ViewPermissionsTestCase, self).setUp()
        self.password = "test password"
        self.course = CourseFactory.create()
        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create(password=self.password)
        self.moderator = UserFactory.create(password=self.password)
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)
        CourseEnrollmentFactory(user=self.moderator, course_id=self.course.id)
        self.moderator.roles.add(Role.objects.get(name="Moderator", course_id=self.course.id))

    def test_pin_thread_as_student(self, mock_request):
        self._set_mock_request_data(mock_request, {})
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse("pin_thread", kwargs={"course_id": unicode(self.course.id), "thread_id": "dummy"})
        )
        self.assertEqual(response.status_code, 401)

    def test_pin_thread_as_moderator(self, mock_request):
        self._set_mock_request_data(mock_request, {})
        self.client.login(username=self.moderator.username, password=self.password)
        response = self.client.post(
            reverse("pin_thread", kwargs={"course_id": unicode(self.course.id), "thread_id": "dummy"})
        )
        self.assertEqual(response.status_code, 200)

    def test_un_pin_thread_as_student(self, mock_request):
        self._set_mock_request_data(mock_request, {})
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse("un_pin_thread", kwargs={"course_id": unicode(self.course.id), "thread_id": "dummy"})
        )
        self.assertEqual(response.status_code, 401)

    def test_un_pin_thread_as_moderator(self, mock_request):
        self._set_mock_request_data(mock_request, {})
        self.client.login(username=self.moderator.username, password=self.password)
        response = self.client.post(
            reverse("un_pin_thread", kwargs={"course_id": unicode(self.course.id), "thread_id": "dummy"})
        )
        self.assertEqual(response.status_code, 200)

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
            reverse("endorse_comment", kwargs={"course_id": unicode(self.course.id), "comment_id": "dummy"})
        )
        self.assertEqual(response.status_code, 200)

    def test_endorse_response_as_student(self, mock_request):
        self._set_mock_request_thread_and_comment(
            mock_request,
            {"type": "thread", "thread_type": "question", "user_id": str(self.moderator.id)},
            {"type": "comment", "thread_id": "dummy"}
        )
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse("endorse_comment", kwargs={"course_id": unicode(self.course.id), "comment_id": "dummy"})
        )
        self.assertEqual(response.status_code, 401)

    def test_endorse_response_as_student_question_author(self, mock_request):
        self._set_mock_request_thread_and_comment(
            mock_request,
            {"type": "thread", "thread_type": "question", "user_id": str(self.student.id)},
            {"type": "comment", "thread_id": "dummy"}
        )
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse("endorse_comment", kwargs={"course_id": unicode(self.course.id), "comment_id": "dummy"})
        )
        self.assertEqual(response.status_code, 200)


class CreateThreadUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin, MockRequestSetupMixin):
    def setUp(self):
        super(CreateThreadUnicodeTestCase, self).setUp()

        self.course = CourseFactory.create()
        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request')
    def _test_unicode_data(self, text, mock_request,):
        """
        Test to make sure unicode data in a thread doesn't break it.
        """
        self._set_mock_request_data(mock_request, {})
        request = RequestFactory().post("dummy_url", {"thread_type": "discussion", "body": text, "title": text})
        request.user = self.student
        request.view_name = "create_thread"
        response = views.create_thread(
            request, course_id=unicode(self.course.id), commentable_id="non_team_dummy_id"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_request.called)
        self.assertEqual(mock_request.call_args[1]["data"]["body"], text)
        self.assertEqual(mock_request.call_args[1]["data"]["title"], text)


@disable_signal(views, 'thread_edited')
class UpdateThreadUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin, MockRequestSetupMixin):
    def setUp(self):
        super(UpdateThreadUnicodeTestCase, self).setUp()

        self.course = CourseFactory.create()
        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('django_comment_client.utils.get_discussion_categories_ids', return_value=["test_commentable"])
    @patch('lms.lib.comment_client.utils.requests.request')
    def _test_unicode_data(self, text, mock_request, mock_get_discussion_id_map):
        self._set_mock_request_data(mock_request, {
            "user_id": str(self.student.id),
            "closed": False,
        })
        request = RequestFactory().post("dummy_url", {"body": text, "title": text, "thread_type": "question", "commentable_id": "test_commentable"})
        request.user = self.student
        request.view_name = "update_thread"
        response = views.update_thread(request, course_id=unicode(self.course.id), thread_id="dummy_thread_id")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_request.called)
        self.assertEqual(mock_request.call_args[1]["data"]["body"], text)
        self.assertEqual(mock_request.call_args[1]["data"]["title"], text)
        self.assertEqual(mock_request.call_args[1]["data"]["thread_type"], "question")
        self.assertEqual(mock_request.call_args[1]["data"]["commentable_id"], "test_commentable")


@disable_signal(views, 'comment_created')
class CreateCommentUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin, MockRequestSetupMixin):
    def setUp(self):
        super(CreateCommentUnicodeTestCase, self).setUp()

        self.course = CourseFactory.create()
        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request')
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
                request, course_id=unicode(self.course.id), thread_id="dummy_thread_id"
            )

            self.assertEqual(response.status_code, 200)
            self.assertTrue(mock_request.called)
            self.assertEqual(mock_request.call_args[1]["data"]["body"], text)
        finally:
            del Thread.commentable_id


@disable_signal(views, 'comment_edited')
class UpdateCommentUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin, MockRequestSetupMixin):
    def setUp(self):
        super(UpdateCommentUnicodeTestCase, self).setUp()

        self.course = CourseFactory.create()
        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request')
    def _test_unicode_data(self, text, mock_request):
        self._set_mock_request_data(mock_request, {
            "user_id": str(self.student.id),
            "closed": False,
        })
        request = RequestFactory().post("dummy_url", {"body": text})
        request.user = self.student
        request.view_name = "update_comment"
        response = views.update_comment(request, course_id=unicode(self.course.id), comment_id="dummy_comment_id")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_request.called)
        self.assertEqual(mock_request.call_args[1]["data"]["body"], text)


@disable_signal(views, 'comment_created')
class CreateSubCommentUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin, MockRequestSetupMixin):
    """
    Make sure comments under a response can handle unicode.
    """
    def setUp(self):
        super(CreateSubCommentUnicodeTestCase, self).setUp()

        self.course = CourseFactory.create()
        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request')
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
                request, course_id=unicode(self.course.id), comment_id="dummy_comment_id"
            )

            self.assertEqual(response.status_code, 200)
            self.assertTrue(mock_request.called)
            self.assertEqual(mock_request.call_args[1]["data"]["body"], text)
        finally:
            del Thread.commentable_id


@ddt.ddt
@patch("lms.lib.comment_client.utils.requests.request")
@disable_signal(views, 'thread_voted')
@disable_signal(views, 'thread_edited')
@disable_signal(views, 'comment_created')
@disable_signal(views, 'comment_voted')
@disable_signal(views, 'comment_deleted')
class TeamsPermissionsTestCase(UrlResetMixin, ModuleStoreTestCase, MockRequestSetupMixin):
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
        ('moderator', 'team_commentable_id', 200)
    ]

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(TeamsPermissionsTestCase, self).setUp()
        self.password = "test password"
        teams_configuration = {
            'topics': [{'id': "topic_id", 'name': 'Solar Power', 'description': 'Solar power is hot'}]
        }
        self.course = CourseFactory.create(teams_configuration=teams_configuration)
        seed_permissions_roles(self.course.id)

        # Create 3 users-- student in team, student not in team, discussion moderator
        self.student_in_team = UserFactory.create(password=self.password)
        self.student_not_in_team = UserFactory.create(password=self.password)
        self.moderator = UserFactory.create(password=self.password)
        CourseEnrollmentFactory(user=self.student_in_team, course_id=self.course.id)
        CourseEnrollmentFactory(user=self.student_not_in_team, course_id=self.course.id)
        CourseEnrollmentFactory(user=self.moderator, course_id=self.course.id)
        self.moderator.roles.add(Role.objects.get(name="Moderator", course_id=self.course.id))

        # Create a team.
        self.team_commentable_id = "team_discussion_id"
        self.team = CourseTeamFactory.create(
            name=u'The Only Team',
            course_id=self.course.id,
            topic_id='topic_id',
            discussion_topic_id=self.team_commentable_id
        )

        self.team.add_user(self.student_in_team)

        # Dummy commentable ID not linked to a team
        self.course_commentable_id = "course_level_commentable"

    def _setup_mock(self, user, mock_request, data):
        user = getattr(self, user)
        self._set_mock_request_data(mock_request, data)
        self.client.login(username=user.username, password=self.password)

    @ddt.data(
        # student_in_team will be able to update his own post, regardless of team membership
        ('student_in_team', 'student_in_team', 'team_commentable_id', 200),
        ('student_in_team', 'student_in_team', 'course_commentable_id', 200),
        # students can only update their own posts
        ('student_in_team', 'moderator', 'team_commentable_id', 401),
        # Even though student_not_in_team is not in the team, he can still modify posts he created while in the team.
        ('student_not_in_team', 'student_not_in_team', 'team_commentable_id', 200),
        # Moderators can change their own posts and other people's posts.
        ('moderator', 'moderator', 'team_commentable_id', 200),
        ('moderator', 'student_in_team', 'team_commentable_id', 200),
    )
    @ddt.unpack
    def test_update_thread(self, user, thread_author, commentable_id, status_code, mock_request):
        """
        Verify that update_thread is limited to thread authors and privileged users (team membership does not matter).
        """
        commentable_id = getattr(self, commentable_id)
        # thread_author is who is marked as the author of the thread being updated.
        thread_author = getattr(self, thread_author)
        self._setup_mock(
            user, mock_request,  # user is the person making the request.
            {
                "user_id": str(thread_author.id),
                "closed": False, "commentable_id": commentable_id,
                "context": "standalone"
            }
        )
        response = self.client.post(
            reverse(
                "update_thread",
                kwargs={
                    "course_id": unicode(self.course.id),
                    "thread_id": "dummy"
                }
            ),
            data={"body": "foo", "title": "foo", "commentable_id": commentable_id}
        )
        self.assertEqual(response.status_code, status_code)

    @ddt.data(
        # Students can delete their own posts
        ('student_in_team', 'student_in_team', 'team_commentable_id', 200),
        # Moderators can delete any post
        ('moderator', 'student_in_team', 'team_commentable_id', 200),
        # Others cannot delete posts
        ('student_in_team', 'moderator', 'team_commentable_id', 401),
        ('student_not_in_team', 'student_in_team', 'team_commentable_id', 401)
    )
    @ddt.unpack
    def test_delete_comment(self, user, comment_author, commentable_id, status_code, mock_request):
        commentable_id = getattr(self, commentable_id)
        comment_author = getattr(self, comment_author)

        self._setup_mock(user, mock_request, {
            "closed": False,
            "commentable_id": commentable_id,
            "user_id": str(comment_author.id)
        })

        response = self.client.post(
            reverse(
                "delete_comment",
                kwargs={
                    "course_id": unicode(self.course.id),
                    "comment_id": "dummy"
                }
            ),
            data={"body": "foo", "title": "foo"}
        )
        self.assertEqual(response.status_code, status_code)

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
                    "course_id": unicode(self.course.id),
                    "thread_id": "dummy"
                }
            ),
            data={"body": "foo", "title": "foo"}
        )
        self.assertEqual(response.status_code, status_code)

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
                    "course_id": unicode(self.course.id),
                    "comment_id": "dummy_comment"
                }
            ),
            data={"body": "foo", "title": "foo"}
        )
        self.assertEqual(response.status_code, status_code)

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
            {"closed": False, "commentable_id": commentable_id, "thread_id": "dummy_thread"},
        )
        for action in ["upvote_comment", "downvote_comment", "un_flag_abuse_for_comment", "flag_abuse_for_comment"]:
            response = self.client.post(
                reverse(
                    action,
                    kwargs={"course_id": unicode(self.course.id), "comment_id": "dummy_comment"}
                )
            )
            self.assertEqual(response.status_code, status_code)

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
            {"closed": False, "commentable_id": commentable_id},
        )
        for action in ["upvote_thread", "downvote_thread", "un_flag_abuse_for_thread", "flag_abuse_for_thread",
                       "follow_thread", "unfollow_thread"]:
            response = self.client.post(
                reverse(
                    action,
                    kwargs={"course_id": unicode(self.course.id), "thread_id": "dummy_thread"}
                )
            )
            self.assertEqual(response.status_code, status_code)

    @ddt.data(*ddt_permissions_args)
    @ddt.unpack
    def test_create_thread(self, user, commentable_id, status_code, __):
        """
        Verify that creation of threads is limited to members of the team or users with 'edit_content' permission.
        """
        commentable_id = getattr(self, commentable_id)
        # mock_request is not used because Commentables don't exist in comment service.
        self.client.login(username=getattr(self, user).username, password=self.password)
        response = self.client.post(
            reverse(
                "create_thread",
                kwargs={"course_id": unicode(self.course.id), "commentable_id": commentable_id}
            ),
            data={"body": "foo", "title": "foo", "thread_type": "discussion"}
        )
        self.assertEqual(response.status_code, status_code)

    @ddt.data(*ddt_permissions_args)
    @ddt.unpack
    def test_commentable_actions(self, user, commentable_id, status_code, __):
        """
        Verify that following of commentables is limited to members of the team or users with
        'edit_content' permission.
        """
        commentable_id = getattr(self, commentable_id)
        # mock_request is not used because Commentables don't exist in comment service.
        self.client.login(username=getattr(self, user).username, password=self.password)
        for action in ["follow_commentable", "unfollow_commentable"]:
            response = self.client.post(
                reverse(
                    action,
                    kwargs={"course_id": unicode(self.course.id), "commentable_id": commentable_id}
                )
            )
            self.assertEqual(response.status_code, status_code)


TEAM_COMMENTABLE_ID = 'test-team-discussion'


@disable_signal(views, 'comment_created')
@ddt.ddt
class ForumEventTestCase(ModuleStoreTestCase, MockRequestSetupMixin):
    """
    Forum actions are expected to launch analytics events. Test these here.
    """
    def setUp(self):
        super(ForumEventTestCase, self).setUp()
        self.course = CourseFactory.create()
        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)
        self.student.roles.add(Role.objects.get(name="Student", course_id=self.course.id))
        CourseAccessRoleFactory(course_id=self.course.id, user=self.student, role='Wizard')

    @patch('eventtracking.tracker.emit')
    @patch('lms.lib.comment_client.utils.requests.request')
    def test_thread_event(self, __, mock_emit):
        request = RequestFactory().post(
            "dummy_url", {
                "thread_type": "discussion",
                "body": "Test text",
                "title": "Test",
                "auto_subscribe": True
            }
        )
        request.user = self.student
        request.view_name = "create_thread"

        views.create_thread(request, course_id=unicode(self.course.id), commentable_id="test_commentable")

        event_name, event = mock_emit.call_args[0]
        self.assertEqual(event_name, 'edx.forum.thread.created')
        self.assertEqual(event['body'], 'Test text')
        self.assertEqual(event['title'], 'Test')
        self.assertEqual(event['commentable_id'], 'test_commentable')
        self.assertEqual(event['user_forums_roles'], ['Student'])
        self.assertEqual(event['options']['followed'], True)
        self.assertEqual(event['user_course_roles'], ['Wizard'])
        self.assertEqual(event['anonymous'], False)
        self.assertEqual(event['group_id'], None)
        self.assertEqual(event['thread_type'], 'discussion')
        self.assertEquals(event['anonymous_to_peers'], False)

    @patch('eventtracking.tracker.emit')
    @patch('lms.lib.comment_client.utils.requests.request')
    def test_response_event(self, mock_request, mock_emit):
        """
        Check to make sure an event is fired when a user responds to a thread.
        """
        mock_request.return_value.status_code = 200
        self._set_mock_request_data(mock_request, {
            "closed": False,
            "commentable_id": 'test_commentable_id',
            'thread_id': 'test_thread_id',
        })
        request = RequestFactory().post("dummy_url", {"body": "Test comment", 'auto_subscribe': True})
        request.user = self.student
        request.view_name = "create_comment"
        views.create_comment(request, course_id=unicode(self.course.id), thread_id='test_thread_id')

        event_name, event = mock_emit.call_args[0]
        self.assertEqual(event_name, 'edx.forum.response.created')
        self.assertEqual(event['body'], "Test comment")
        self.assertEqual(event['commentable_id'], 'test_commentable_id')
        self.assertEqual(event['user_forums_roles'], ['Student'])
        self.assertEqual(event['user_course_roles'], ['Wizard'])
        self.assertEqual(event['discussion']['id'], 'test_thread_id')
        self.assertEqual(event['options']['followed'], True)

    @patch('eventtracking.tracker.emit')
    @patch('lms.lib.comment_client.utils.requests.request')
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
        views.create_sub_comment(request, course_id=unicode(self.course.id), comment_id="dummy_comment_id")

        event_name, event = mock_emit.call_args[0]
        self.assertEqual(event_name, "edx.forum.comment.created")
        self.assertEqual(event['body'], 'Another comment')
        self.assertEqual(event['discussion']['id'], 'test_thread_id')
        self.assertEqual(event['response']['id'], 'test_response_id')
        self.assertEqual(event['user_forums_roles'], ['Student'])
        self.assertEqual(event['user_course_roles'], ['Wizard'])
        self.assertEqual(event['options']['followed'], False)

    @patch('eventtracking.tracker.emit')
    @patch('lms.lib.comment_client.utils.requests.request')
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

        mock_request.return_value.status_code = 200
        self._set_mock_request_data(mock_request, {
            'closed': False,
            'commentable_id': TEAM_COMMENTABLE_ID,
            'thread_id': 'test_thread_id',
        })

        request = RequestFactory().post('dummy_url', view_data)
        request.user = user
        request.view_name = view_name

        getattr(views, view_name)(request, course_id=unicode(self.course.id), **view_kwargs)

        name, event = mock_emit.call_args[0]
        self.assertEqual(name, event_name)
        self.assertEqual(event['team_id'], team.team_id)


class UsersEndpointTestCase(ModuleStoreTestCase, MockRequestSetupMixin):

    def set_post_counts(self, mock_request, threads_count=1, comments_count=1):
        """
        sets up a mock response from the comments service for getting post counts for our other_user
        """
        self._set_mock_request_data(mock_request, {
            "threads_count": threads_count,
            "comments_count": comments_count,
        })

    def setUp(self):
        super(UsersEndpointTestCase, self).setUp()

        self.course = CourseFactory.create()
        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        self.enrollment = CourseEnrollmentFactory(user=self.student, course_id=self.course.id)
        self.other_user = UserFactory.create(username="other")
        CourseEnrollmentFactory(user=self.other_user, course_id=self.course.id)

    def make_request(self, method='get', course_id=None, **kwargs):
        course_id = course_id or self.course.id
        request = getattr(RequestFactory(), method)("dummy_url", kwargs)
        request.user = self.student
        request.view_name = "users"
        return views.users(request, course_id=course_id.to_deprecated_string())

    @patch('lms.lib.comment_client.utils.requests.request')
    def test_finds_exact_match(self, mock_request):
        self.set_post_counts(mock_request)
        response = self.make_request(username="other")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)["users"],
            [{"id": self.other_user.id, "username": self.other_user.username}]
        )

    @patch('lms.lib.comment_client.utils.requests.request')
    def test_finds_no_match(self, mock_request):
        self.set_post_counts(mock_request)
        response = self.make_request(username="othor")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["users"], [])

    def test_requires_GET(self):
        response = self.make_request(method='post', username="other")
        self.assertEqual(response.status_code, 405)

    def test_requires_username_param(self):
        response = self.make_request()
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content)
        self.assertIn("errors", content)
        self.assertNotIn("users", content)

    def test_course_does_not_exist(self):
        course_id = SlashSeparatedCourseKey.from_deprecated_string("does/not/exist")
        response = self.make_request(course_id=course_id, username="other")

        self.assertEqual(response.status_code, 404)
        content = json.loads(response.content)
        self.assertIn("errors", content)
        self.assertNotIn("users", content)

    def test_requires_requestor_enrolled_in_course(self):
        # unenroll self.student from the course.
        self.enrollment.delete()

        response = self.make_request(username="other")
        self.assertEqual(response.status_code, 404)
        content = json.loads(response.content)
        self.assertIn("errors", content)
        self.assertNotIn("users", content)

    @patch('lms.lib.comment_client.utils.requests.request')
    def test_requires_matched_user_has_forum_content(self, mock_request):
        self.set_post_counts(mock_request, 0, 0)
        response = self.make_request(username="other")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["users"], [])

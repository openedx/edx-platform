import logging
import json

from django.test.utils import override_settings
from django.test.client import Client, RequestFactory
from django.contrib.auth.models import User
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command
from util.testing import UrlResetMixin
from django_comment_common.models import Role
from django_comment_common.utils import seed_permissions_roles
from django_comment_client.base import views
from django_comment_client.tests.unicode import UnicodeTestMixin

from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from nose.tools import assert_true, assert_equal  # pylint: disable=E0611
from mock import patch, ANY

log = logging.getLogger(__name__)

CS_PREFIX = "http://localhost:4567/api/v1"


class MockRequestSetupMixin(object):
    def _set_mock_request_data(self, mock_request, data):
        mock_request.return_value.text = json.dumps(data)
        mock_request.return_value.json.return_value = data


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
@patch('lms.lib.comment_client.utils.requests.request')
class ViewsTestCase(UrlResetMixin, ModuleStoreTestCase, MockRequestSetupMixin):

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):

        # Patching the ENABLE_DISCUSSION_SERVICE value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super(ViewsTestCase, self).setUp()

        # create a course
        self.course = CourseFactory.create(org='MITx', course='999',
                                           display_name='Robot Super Course')
        self.course_id = self.course.id
        # seed the forums permissions and roles
        call_command('seed_permissions_roles', self.course_id.to_deprecated_string())

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('student.models.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            password = 'test'

            # Create the user and make them active so we can log them in.
            self.student = User.objects.create_user(uname, email, password)
            self.student.is_active = True
            self.student.save()

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student,
                                    course_id=self.course_id)

            self.client = Client()
            assert_true(self.client.login(username='student', password='test'))

    def test_create_thread(self, mock_request):
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
        thread = {"body": ["this is a post"],
                  "anonymous_to_peers": ["false"],
                  "auto_subscribe": ["false"],
                  "anonymous": ["false"],
                  "title": ["Hello"]
                  }
        url = reverse('create_thread', kwargs={'commentable_id': 'i4x-MITx-999-course-Robot_Super_Course',
                                               'course_id': self.course_id.to_deprecated_string()})
        response = self.client.post(url, data=thread)
        assert_true(mock_request.called)
        mock_request.assert_called_with(
            'post',
            '{prefix}/i4x-MITx-999-course-Robot_Super_Course/threads'.format(prefix=CS_PREFIX),
            data={
                'body': u'this is a post',
                'anonymous_to_peers': False, 'user_id': 1,
                'title': u'Hello',
                'commentable_id': u'i4x-MITx-999-course-Robot_Super_Course',
                'anonymous': False,
                'course_id': u'MITx/999/Robot_Super_Course',
            },
            params={'request_id': ANY},
            headers=ANY,
            timeout=5
        )
        assert_equal(response.status_code, 200)

    def test_delete_comment(self, mock_request):
        self._set_mock_request_data(mock_request, {
            "user_id": str(self.student.id),
            "closed": False,
        })
        test_comment_id = "test_comment_id"
        request = RequestFactory().post("dummy_url", {"id": test_comment_id})
        request.user = self.student
        request.view_name = "delete_comment"
        response = views.delete_comment(request, course_id=self.course.id.to_deprecated_string(), comment_id=test_comment_id)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_request.called)
        args = mock_request.call_args[0]
        self.assertEqual(args[0], "delete")
        self.assertTrue(args[1].endswith("/{}".format(test_comment_id)))

    def _setup_mock_request(self, mock_request, include_depth=False):
        """
        Ensure that mock_request returns the data necessary to make views
        function correctly
        """
        mock_request.return_value.status_code = 200
        data = {
            "user_id": str(self.student.id),
            "closed": False,
        }
        if include_depth:
            data["depth"] = 0
        self._set_mock_request_data(mock_request, data)

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
            {"commentable_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {"body": "foo"},
            mock_request
        )

    def test_create_thread_empty_title(self, mock_request):
        self._test_request_error(
            "create_thread",
            {"commentable_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {"body": "foo", "title": " "},
            mock_request
        )

    def test_create_thread_no_body(self, mock_request):
        self._test_request_error(
            "create_thread",
            {"commentable_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {"title": "foo"},
            mock_request
        )

    def test_create_thread_empty_body(self, mock_request):
        self._test_request_error(
            "create_thread",
            {"commentable_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {"body": " ", "title": "foo"},
            mock_request
        )

    def test_update_thread_no_title(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {"body": "foo"},
            mock_request
        )

    def test_update_thread_empty_title(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {"body": "foo", "title": " "},
            mock_request
        )

    def test_update_thread_no_body(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {"title": "foo"},
            mock_request
        )

    def test_update_thread_empty_body(self, mock_request):
        self._test_request_error(
            "update_thread",
            {"thread_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {"body": " ", "title": "foo"},
            mock_request
        )

    def test_create_comment_no_body(self, mock_request):
        self._test_request_error(
            "create_comment",
            {"thread_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {},
            mock_request
        )

    def test_create_comment_empty_body(self, mock_request):
        self._test_request_error(
            "create_comment",
            {"thread_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {"body": " "},
            mock_request
        )

    def test_create_sub_comment_no_body(self, mock_request):
        self._test_request_error(
            "create_sub_comment",
            {"comment_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {},
            mock_request
        )

    def test_create_sub_comment_empty_body(self, mock_request):
        self._test_request_error(
            "create_sub_comment",
            {"comment_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {"body": " "},
            mock_request
        )

    def test_update_comment_no_body(self, mock_request):
        self._test_request_error(
            "update_comment",
            {"comment_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {},
            mock_request
        )

    def test_update_comment_empty_body(self, mock_request):
        self._test_request_error(
            "update_comment",
            {"comment_id": "dummy", "course_id": self.course_id.to_deprecated_string()},
            {"body": " "},
            mock_request
        )

    def test_update_comment_basic(self, mock_request):
        self._setup_mock_request(mock_request)
        comment_id = "test_comment_id"
        updated_body = "updated body"

        response = self.client.post(
            reverse(
                "update_comment",
                kwargs={"course_id": self.course_id.to_deprecated_string(), "comment_id": comment_id}
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

    def test_flag_thread(self, mock_request):
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
            "closed": False,
            "id": "518d4237b023791dca00000d",
            "user_id": "1","username": "robot",
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
        url = reverse('flag_abuse_for_thread', kwargs={'thread_id': '518d4237b023791dca00000d', 'course_id': self.course_id.to_deprecated_string()})
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

    def test_un_flag_thread(self, mock_request):
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
            "comments_count": 0
        })
        url = reverse('un_flag_abuse_for_thread', kwargs={'thread_id': '518d4237b023791dca00000d', 'course_id': self.course_id.to_deprecated_string()})
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

    def test_flag_comment(self, mock_request):
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
            "abuse_flaggers": [1],
            "type": "comment",
            "endorsed": False
        })
        url = reverse('flag_abuse_for_comment', kwargs={'comment_id': '518d4237b023791dca00000d', 'course_id': self.course_id.to_deprecated_string()})
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

    def test_un_flag_comment(self, mock_request):
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
            "type": "comment",
            "endorsed": False
        })
        url = reverse('un_flag_abuse_for_comment', kwargs={'comment_id': '518d4237b023791dca00000d', 'course_id': self.course_id.to_deprecated_string()})
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

@patch("lms.lib.comment_client.utils.requests.request")
@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
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
            reverse("pin_thread", kwargs={"course_id": self.course.id.to_deprecated_string(), "thread_id": "dummy"})
        )
        self.assertEqual(response.status_code, 401)

    def test_pin_thread_as_moderator(self, mock_request):
        self._set_mock_request_data(mock_request, {})
        self.client.login(username=self.moderator.username, password=self.password)
        response = self.client.post(
            reverse("pin_thread", kwargs={"course_id": self.course.id.to_deprecated_string(), "thread_id": "dummy"})
        )
        self.assertEqual(response.status_code, 200)

    def test_un_pin_thread_as_student(self, mock_request):
        self._set_mock_request_data(mock_request, {})
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.post(
            reverse("un_pin_thread", kwargs={"course_id": self.course.id.to_deprecated_string(), "thread_id": "dummy"})
        )
        self.assertEqual(response.status_code, 401)

    def test_un_pin_thread_as_moderator(self, mock_request):
        self._set_mock_request_data(mock_request, {})
        self.client.login(username=self.moderator.username, password=self.password)
        response = self.client.post(
            reverse("un_pin_thread", kwargs={"course_id": self.course.id.to_deprecated_string(), "thread_id": "dummy"})
        )
        self.assertEqual(response.status_code, 200)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class CreateThreadUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin, MockRequestSetupMixin):
    def setUp(self):
        self.course = CourseFactory.create()
        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request')
    def _test_unicode_data(self, text, mock_request):
        self._set_mock_request_data(mock_request, {})
        request = RequestFactory().post("dummy_url", {"body": text, "title": text})
        request.user = self.student
        request.view_name = "create_thread"
        response = views.create_thread(request, course_id=self.course.id.to_deprecated_string(), commentable_id="test_commentable")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_request.called)
        self.assertEqual(mock_request.call_args[1]["data"]["body"], text)
        self.assertEqual(mock_request.call_args[1]["data"]["title"], text)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class UpdateThreadUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin, MockRequestSetupMixin):
    def setUp(self):
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
        request = RequestFactory().post("dummy_url", {"body": text, "title": text})
        request.user = self.student
        request.view_name = "update_thread"
        response = views.update_thread(request, course_id=self.course.id.to_deprecated_string(), thread_id="dummy_thread_id")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_request.called)
        self.assertEqual(mock_request.call_args[1]["data"]["body"], text)
        self.assertEqual(mock_request.call_args[1]["data"]["title"], text)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class CreateCommentUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin, MockRequestSetupMixin):
    def setUp(self):
        self.course = CourseFactory.create()
        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request')
    def _test_unicode_data(self, text, mock_request):
        self._set_mock_request_data(mock_request, {
            "closed": False,
        })
        request = RequestFactory().post("dummy_url", {"body": text})
        request.user = self.student
        request.view_name = "create_comment"
        response = views.create_comment(request, course_id=self.course.id.to_deprecated_string(), thread_id="dummy_thread_id")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_request.called)
        self.assertEqual(mock_request.call_args[1]["data"]["body"], text)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class UpdateCommentUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin, MockRequestSetupMixin):
    def setUp(self):
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
        response = views.update_comment(request, course_id=self.course.id.to_deprecated_string(), comment_id="dummy_comment_id")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_request.called)
        self.assertEqual(mock_request.call_args[1]["data"]["body"], text)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class CreateSubCommentUnicodeTestCase(ModuleStoreTestCase, UnicodeTestMixin, MockRequestSetupMixin):
    def setUp(self):
        self.course = CourseFactory.create()
        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

    @patch('lms.lib.comment_client.utils.requests.request')
    def _test_unicode_data(self, text, mock_request):
        self._set_mock_request_data(mock_request, {
            "closed": False,
            "depth": 1,
        })
        request = RequestFactory().post("dummy_url", {"body": text})
        request.user = self.student
        request.view_name = "create_sub_comment"
        response = views.create_sub_comment(request, course_id=self.course.id.to_deprecated_string(), comment_id="dummy_comment_id")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_request.called)
        self.assertEqual(mock_request.call_args[1]["data"]["body"], text)

import logging

from django.test.utils import override_settings
from django.test.client import Client
from django.contrib.auth.models import User
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command
from util.testing import UrlResetMixin

from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from nose.tools import assert_true, assert_equal  # pylint: disable=E0611
from mock import patch, ANY

log = logging.getLogger(__name__)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
@patch('lms.lib.comment_client.utils.requests.request')
class ViewsTestCase(UrlResetMixin, ModuleStoreTestCase):

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
        call_command('seed_permissions_roles', self.course_id)

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
        mock_request.return_value.text = u'{"title":"Hello",\
                                            "body":"this is a post",\
                                            "course_id":"MITx/999/Robot_Super_Course",\
                                            "anonymous":false,\
                                            "anonymous_to_peers":false,\
                                            "commentable_id":"i4x-MITx-999-course-Robot_Super_Course",\
                                            "created_at":"2013-05-10T18:53:43Z",\
                                            "updated_at":"2013-05-10T18:53:43Z",\
                                            "at_position_list":[],\
                                            "closed":false,\
                                            "id":"518d4237b023791dca00000d",\
                                            "user_id":"1","username":"robot",\
                                            "votes":{"count":0,"up_count":0,\
                                            "down_count":0,"point":0},\
                                            "abuse_flaggers":[],\
                                            "type":"thread","group_id":null,\
                                            "pinned":false,\
                                            "endorsed":false,\
                                            "unread_comments_count":0,\
                                            "read":false,"comments_count":0}'
        thread = {"body": ["this is a post"],
                  "anonymous_to_peers": ["false"],
                  "auto_subscribe": ["false"],
                  "anonymous": ["false"],
                  "title": ["Hello"]
                  }
        url = reverse('create_thread', kwargs={'commentable_id': 'i4x-MITx-999-course-Robot_Super_Course',
                                               'course_id': self.course_id})
        response = self.client.post(url, data=thread)
        assert_true(mock_request.called)
        mock_request.assert_called_with(
            'post',
            'http://localhost:4567/api/v1/i4x-MITx-999-course-Robot_Super_Course/threads',
            data={
                'body': u'this is a post',
                'anonymous_to_peers': False, 'user_id': 1,
                'title': u'Hello',
                'commentable_id': u'i4x-MITx-999-course-Robot_Super_Course',
                'anonymous': False, 'course_id': u'MITx/999/Robot_Super_Course',
            },
            params={'request_id': ANY},
            headers={'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
            timeout=5
        )
        assert_equal(response.status_code, 200)

    def test_flag_thread(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = u'{"title":"Hello",\
                                            "body":"this is a post",\
                                            "course_id":"MITx/999/Robot_Super_Course",\
                                            "anonymous":false,\
                                            "anonymous_to_peers":false,\
                                            "commentable_id":"i4x-MITx-999-course-Robot_Super_Course",\
                                            "created_at":"2013-05-10T18:53:43Z",\
                                            "updated_at":"2013-05-10T18:53:43Z",\
                                            "at_position_list":[],\
                                            "closed":false,\
                                            "id":"518d4237b023791dca00000d",\
                                            "user_id":"1","username":"robot",\
                                            "votes":{"count":0,"up_count":0,\
                                            "down_count":0,"point":0},\
                                            "abuse_flaggers":[1],\
                                            "type":"thread","group_id":null,\
                                            "pinned":false,\
                                            "endorsed":false,\
                                            "unread_comments_count":0,\
                                            "read":false,"comments_count":0}'
        url = reverse('flag_abuse_for_thread', kwargs={'thread_id': '518d4237b023791dca00000d', 'course_id': self.course_id})
        response = self.client.post(url)
        assert_true(mock_request.called)

        call_list = [
            (
                ('get', 'http://localhost:4567/api/v1/threads/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            ),
            (
                ('put', 'http://localhost:4567/api/v1/threads/518d4237b023791dca00000d/abuse_flag'),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            ),
            (
                ('get', 'http://localhost:4567/api/v1/threads/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            )
        ]

        assert_equal(call_list, mock_request.call_args_list)

        assert_equal(response.status_code, 200)

    def test_un_flag_thread(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = u'{"title":"Hello",\
                                            "body":"this is a post",\
                                            "course_id":"MITx/999/Robot_Super_Course",\
                                            "anonymous":false,\
                                            "anonymous_to_peers":false,\
                                            "commentable_id":"i4x-MITx-999-course-Robot_Super_Course",\
                                            "created_at":"2013-05-10T18:53:43Z",\
                                            "updated_at":"2013-05-10T18:53:43Z",\
                                            "at_position_list":[],\
                                            "closed":false,\
                                            "id":"518d4237b023791dca00000d",\
                                            "user_id":"1","username":"robot",\
                                            "votes":{"count":0,"up_count":0,\
                                            "down_count":0,"point":0},\
                                            "abuse_flaggers":[],\
                                            "type":"thread","group_id":null,\
                                            "pinned":false,\
                                            "endorsed":false,\
                                            "unread_comments_count":0,\
                                            "read":false,"comments_count":0}'
        url = reverse('un_flag_abuse_for_thread', kwargs={'thread_id': '518d4237b023791dca00000d', 'course_id': self.course_id})
        response = self.client.post(url)
        assert_true(mock_request.called)

        call_list = [
            (
                ('get', 'http://localhost:4567/api/v1/threads/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            ),
            (
                ('put', 'http://localhost:4567/api/v1/threads/518d4237b023791dca00000d/abuse_unflag'),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            ),
            (
                ('get', 'http://localhost:4567/api/v1/threads/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'mark_as_read': True, 'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            )
        ]

        assert_equal(call_list, mock_request.call_args_list)

        assert_equal(response.status_code, 200)

    def test_flag_comment(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = u'{"body":"this is a comment",\
                                            "course_id":"MITx/999/Robot_Super_Course",\
                                            "anonymous":false,\
                                            "anonymous_to_peers":false,\
                                            "commentable_id":"i4x-MITx-999-course-Robot_Super_Course",\
                                            "created_at":"2013-05-10T18:53:43Z",\
                                            "updated_at":"2013-05-10T18:53:43Z",\
                                            "at_position_list":[],\
                                            "closed":false,\
                                            "id":"518d4237b023791dca00000d",\
                                            "user_id":"1","username":"robot",\
                                            "votes":{"count":0,"up_count":0,\
                                            "down_count":0,"point":0},\
                                            "abuse_flaggers":[1],\
                                            "type":"comment",\
                                            "endorsed":false}'
        url = reverse('flag_abuse_for_comment', kwargs={'comment_id': '518d4237b023791dca00000d', 'course_id': self.course_id})
        response = self.client.post(url)
        assert_true(mock_request.called)

        call_list = [
            (
                ('get', 'http://localhost:4567/api/v1/comments/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            ),
            (
                ('put', 'http://localhost:4567/api/v1/comments/518d4237b023791dca00000d/abuse_flag'),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            ),
            (
                ('get', 'http://localhost:4567/api/v1/comments/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            )
        ]

        assert_equal(call_list, mock_request.call_args_list)

        assert_equal(response.status_code, 200)

    def test_un_flag_comment(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = u'{"body":"this is a comment",\
                                            "course_id":"MITx/999/Robot_Super_Course",\
                                            "anonymous":false,\
                                            "anonymous_to_peers":false,\
                                            "commentable_id":"i4x-MITx-999-course-Robot_Super_Course",\
                                            "created_at":"2013-05-10T18:53:43Z",\
                                            "updated_at":"2013-05-10T18:53:43Z",\
                                            "at_position_list":[],\
                                            "closed":false,\
                                            "id":"518d4237b023791dca00000d",\
                                            "user_id":"1","username":"robot",\
                                            "votes":{"count":0,"up_count":0,\
                                            "down_count":0,"point":0},\
                                            "abuse_flaggers":[],\
                                            "type":"comment",\
                                            "endorsed":false}'
        url = reverse('un_flag_abuse_for_comment', kwargs={'comment_id': '518d4237b023791dca00000d', 'course_id': self.course_id})
        response = self.client.post(url)
        assert_true(mock_request.called)

        call_list = [
            (
                ('get', 'http://localhost:4567/api/v1/comments/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            ),
            (
                ('put', 'http://localhost:4567/api/v1/comments/518d4237b023791dca00000d/abuse_unflag'),
                {
                    'data': {'user_id': '1'},
                    'params': {'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            ),
            (
                ('get', 'http://localhost:4567/api/v1/comments/518d4237b023791dca00000d'),
                {
                    'data': None,
                    'params': {'request_id': ANY},
                    'headers': {'X-Edx-Api-Key': 'PUT_YOUR_API_KEY_HERE'},
                    'timeout': 5
                }
            )
        ]

        assert_equal(call_list, mock_request.call_args_list)

        assert_equal(response.status_code, 200)

from django.test.utils import override_settings
from django.test.client import Client
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from django.core.urlresolvers import reverse
from util.testing import UrlResetMixin

from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from nose.tools import assert_true  # pylint: disable=E0611
from mock import patch, Mock

import logging

log = logging.getLogger(__name__)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class ViewsExceptionTestCase(UrlResetMixin, ModuleStoreTestCase):

    @patch.dict("django.conf.settings.MITX_FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
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
                      kwargs={'course_id': self.course.id, 'user_id': '12345'})  # There is no user 12345
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
                      kwargs={'course_id': self.course.id, 'user_id': '12345'})  # There is no user 12345
        self.response = self.client.get(url)
        self.assertEqual(self.response.status_code, 404)

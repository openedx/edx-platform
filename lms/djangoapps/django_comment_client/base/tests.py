import logging

from django.test.utils import override_settings
from django.test.client import Client
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from django.core.urlresolvers import reverse

from django.core.management import call_command

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from nose.tools import assert_true, assert_equal

log = logging.getLogger(__name__)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class ViewsTestCase(ModuleStoreTestCase):
    def setUp(self):
        # create a course
        self.course = CourseFactory.create(org='MITx', course='999',
                                           display_name='Robot Super Course')
        self.course_id = self.course.id

        # seed the forums permissions and roles
        call_command('seed_permissions_roles', self.course_id)

        self.student = UserFactory(username='student', password='test',
                                   email='student@edx.org')
        self.enrollment = CourseEnrollmentFactory(user=self.student,
                                                  course_id=self.course_id)

        self.client = Client()
        assert_true(self.client.login(username='student', password='test'))

    def test_create_thread(self):
        thread = {"body": ["this is a post"],
                  "anonymous_to_peers": ["false"],
                  "auto_subscribe": ["true"],
                  "anonymous": ["false"],
                  "title": ["Hello"]
                  }
        url = reverse('create_thread',
                      kwargs={'commentable_id': 'i4x-MITx-999-course-Robot_Super_Course',
                              'course_id': self.course_id})
        # url = '/courses/MITx/999/Robot_Super_Course/discussion/i4x-MITx-999-course-Robot_Super_Course/threads/create'
        # url = 'MITx/999/Robot_Super_Course/threads/create'
        response = self.client.post(url, data=thread)
        assert_equal(response.status_code, 200)

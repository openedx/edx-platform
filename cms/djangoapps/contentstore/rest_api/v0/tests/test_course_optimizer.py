from cms.djangoapps.contentstore.tests.test_utils import AuthorizeStaffTestCase
from common.djangoapps.student.tests.factories import InstructorFactory
from rest_framework import status
from django.test import TestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from django.urls import reverse

class TestCourseOptimizer(AuthorizeStaffTestCase, ModuleStoreTestCase, TestCase):
    '''
    Tests for CourseOptimizer
    '''
    def test_inherited(self):
        # This method ensures that pytest recognizes this class as containing tests
        pass

    def make_request(self, course_id=None, data=None):
        url = self.get_url(self.course.id)
        print('make_request url: ', url)
        response = self.client.get(url, data)
        print('make_request response status code: ', response.status_code)
        print('make_request response content: ', response.content)
        return response

    def get_url(self, course_key):
        url = reverse(
            'cms.djangoapps.contentstore:v0:link_check_status',
            kwargs={'course_id': self.course.id}
        )
        print('get_url: ', url)
        return url

    def test_course_instructor(self, expect_status=status.HTTP_200_OK):
        self.course_instructor = InstructorFactory(
            username='instructor',
            password=self.password,
            course_key=self.course.id,
        )
        self.client.login(username=self.course_instructor.username, password=self.password)
        response = self.make_request()
        print('test_course_instructor response status code: ', response.status_code)
        assert response.status_code == expect_status
        return response

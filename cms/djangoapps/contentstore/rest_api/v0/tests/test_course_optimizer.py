from cms.djangoapps.contentstore.tests.test_utils import AuthorizeStaffTestCase
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
        return self.client.get(self.get_url(course_id), data)

    def get_url(self, course_key):
        return reverse(
            'cms.djangoapps.contentstore:v0:link_check_status',
            kwargs={'course_id': 'course-v1:someOrg+someCourse+someRun'}
        )

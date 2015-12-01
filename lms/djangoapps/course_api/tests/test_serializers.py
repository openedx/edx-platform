"""
Test data created by CourseSerializer
"""

from datetime import datetime

from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.course_module import DEFAULT_START_DATE

from ..serializers import CourseSerializer
from .mixins import CourseApiFactoryMixin


class TestCourseSerializerFields(CourseApiFactoryMixin, ModuleStoreTestCase):
    """
    Test variations of start_date field responses
    """

    def setUp(self):
        super(TestCourseSerializerFields, self).setUp()
        self.staff_user = self.create_user('staff', is_staff=True)
        self.honor_user = self.create_user('honor', is_staff=False)
        self.request_factory = APIRequestFactory()

    def _get_request(self, user=None):
        """
        Build a Request object for the specified user
        """
        if user is None:
            user = self.honor_user
        request = Request(self.request_factory.get('/'))
        request.user = user
        return request

    def test_advertised_start(self):
        course = self.create_course(
            course=u'custom',
            start=datetime(2015, 3, 15),
            advertised_start=u'The Ides of March'
        )
        result = CourseSerializer(course, context={'request': self._get_request()}).data
        self.assertEqual(result['course_id'], u'edX/custom/2012_Fall')
        self.assertEqual(result['start_type'], u'string')
        self.assertEqual(result['start_display'], u'The Ides of March')

    def test_empty_start(self):
        course = self.create_course(start=DEFAULT_START_DATE, course=u'custom')
        result = CourseSerializer(course, context={'request': self._get_request()}).data
        self.assertEqual(result['course_id'], u'edX/custom/2012_Fall')
        self.assertEqual(result['start_type'], u'empty')
        self.assertIsNone(result['start_display'])

    def test_description(self):
        course = self.create_course()
        result = CourseSerializer(course, context={'request': self._get_request()}).data
        self.assertEqual(result['description'], u'A course about toys.')

    def test_blocks_url(self):
        course = self.create_course()
        result = CourseSerializer(course, context={'request': self._get_request()}).data
        self.assertEqual(
            result['blocks_url'],
            u'http://testserver/api/courses/v1/blocks/?course_id=edX%2Ftoy%2F2012_Fall'
        )

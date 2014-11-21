"""
Tests for the DjangoXBlockCourseService.
"""
import unittest

from xblock_django.course_service import DjangoXBlockCourseService
from xmodule.modulestore.tests.factories import CourseFactory

class CourseServiceTestCase(unittest.TestCase):
    """
    Tests for the DjangoXBlockCourseService.
    """
    def setUp(self):
        self.course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')

    def assert_xblock_course_matches_django(self, xb_course, course):
        """
        A set of assertions for comparing a XBlockCourse to a django Course
        """
        self.assertEqual(xb_course.id, course.id)
        self.assertEqual(xb_course.display_name, course.display_name)
        self.assertEqual(xb_course.org, course.org)
        self.assertEqual(xb_course.number, course.number)

    def test_convert_course(self):
        """
        Tests for convert_django_course_to_xblock_course behavior
        """
        django_course_service = DjangoXBlockCourseService(self.course.id)
        xb_course = django_course_service.get_current_course()
        self.assert_xblock_course_matches_django(xb_course, self.course)

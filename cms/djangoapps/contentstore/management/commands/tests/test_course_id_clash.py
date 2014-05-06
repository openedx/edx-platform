import sys
from StringIO import StringIO
from django.test import TestCase
from django.core.management import call_command
from xmodule.modulestore.tests.factories import CourseFactory

class ClashIdTestCase(TestCase):
    """
    Test for course_id_clash.
    """
    def test_course_clash(self):
        """
        Test for course_id_clash.
        """
        expected = []
        # clashing courses
        course = CourseFactory.create(org="test", course="courseid", display_name="run1")
        expected.append(course.id)
        course = CourseFactory.create(org="TEST", course="courseid", display_name="RUN12")
        expected.append(course.id)
        course = CourseFactory.create(org="test", course="CourseId", display_name="aRUN123")
        expected.append(course.id)
        # not clashing courses
        not_expected = []
        course = CourseFactory.create(org="test", course="course2", display_name="run1")
        not_expected.append(course.id)
        course = CourseFactory.create(org="test1", course="courseid", display_name="run1")
        not_expected.append(course.id)
        course = CourseFactory.create(org="test", course="courseid0", display_name="run1")
        not_expected.append(course.id)

        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        call_command('course_id_clash', stdout=mystdout)
        sys.stdout = old_stdout
        result = mystdout.getvalue()
        for courseid in expected:
            self.assertIn(courseid.to_deprecated_string(), result)
        for courseid in not_expected:
            self.assertNotIn(courseid.to_deprecated_string(), result)

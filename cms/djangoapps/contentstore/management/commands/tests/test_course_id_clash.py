import sys
from StringIO import StringIO
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from django.core.management import call_command
from xmodule.modulestore.tests.factories import ItemFactory
from opaque_keys.edx.keys import UsageKey, CourseKey

class ClashIdTestCase(ModuleStoreTestCase):
    """
    Test for course_id_clash.
    """
    def test_course_clash(self):
        """
        Test for course_id_clash.
        """
        expected = []
        # CourseFactory doesn't let you create clashing courses. Use ItemFactory to work around this

        # clashing courses
        course = ItemFactory.create(location=CourseKey.from_string('test/courseid/run1').make_usage_key('course', 'run1'), parent_location=None, category='course')
        expected.append(course.id)
        course = ItemFactory.create(location=CourseKey.from_string('TEST/courseid/RUN12').make_usage_key('course', 'RUN12'), parent_location=None, category='course')
        expected.append(course.id)
        course = ItemFactory.create(location=CourseKey.from_string('test/CourseId/aRUN123').make_usage_key('course', 'aRUN123'), parent_location=None, category='course')
        expected.append(course.id)
        # not clashing courses
        not_expected = []
        course = ItemFactory.create(location=CourseKey.from_string('test/course2/run1').make_usage_key('course', 'run1'), parent_location=None, category='course')
        not_expected.append(course.id)
        course = ItemFactory.create(location=CourseKey.from_string('test1/courseid/run1').make_usage_key('course', 'run1'), parent_location=None, category='course')
        not_expected.append(course.id)
        course = ItemFactory.create(location=CourseKey.from_string('test/courseid0/run1').make_usage_key('course', 'run1'), parent_location=None, category='course')
        not_expected.append(course.id)

        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        call_command('course_id_clash', stdout=mystdout)
        sys.stdout = old_stdout
        result = mystdout.getvalue()
        for courseid in expected:
            self.assertIn(unicode(courseid), result)
        for courseid in not_expected:
            self.assertNotIn(unicode(courseid), result)

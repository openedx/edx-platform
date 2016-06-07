# pylint: disable=missing-docstring
from django.core.management.base import CommandError
from mock import patch
from nose.plugins.attrib import attr
from openedx.core.djangoapps.content.course_overviews.management.commands import generate_course_overview
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@attr('shard_2')
class TestGenerateCourseOverview(ModuleStoreTestCase):
    """
    Tests course overview management command.
    """
    def setUp(self):
        """
        Create courses in modulestore.
        """
        super(TestGenerateCourseOverview, self).setUp()
        self.course_key_1 = CourseFactory.create().id
        self.course_key_2 = CourseFactory.create().id
        self.command = generate_course_overview.Command()

    def _assert_courses_not_in_overview(self, *courses):
        """
        Assert that courses doesn't exist in the course overviews.
        """
        course_keys = CourseOverview.get_all_course_keys()
        for expected_course_key in courses:
            self.assertNotIn(expected_course_key, course_keys)

    def _assert_courses_in_overview(self, *courses):
        """
        Assert courses exists in course overviews.
        """
        course_keys = CourseOverview.get_all_course_keys()
        for expected_course_key in courses:
            self.assertIn(expected_course_key, course_keys)

    def test_generate_all(self):
        """
        Test that all courses in the modulestore are loaded into course overviews.
        """
        # ensure that the newly created courses aren't in course overviews
        self._assert_courses_not_in_overview(self.course_key_1, self.course_key_2)
        self.command.handle(all=True)

        # CourseOverview will be populated with all courses in the modulestore
        self._assert_courses_in_overview(self.course_key_1, self.course_key_2)

    def test_generate_one(self):
        """
        Test that a specified course is loaded into course overviews.
        """
        self._assert_courses_not_in_overview(self.course_key_1, self.course_key_2)
        self.command.handle(unicode(self.course_key_1), all=False)
        self._assert_courses_in_overview(self.course_key_1)
        self._assert_courses_not_in_overview(self.course_key_2)

    def test_invalid_key(self):
        """
        Test that CommandError is raised for invalid key.
        """
        with self.assertRaises(CommandError):
            self.command.handle('not/found', all=False)

    @patch('openedx.core.djangoapps.content.course_overviews.models.log')
    def test_not_found_key(self, mock_log):
        """
        Test keys not found are logged.
        """
        self.command.handle('fake/course/id', all=False)
        self.assertTrue(mock_log.exception.called)

    def test_no_params(self):
        """
        Test exception raised when no parameters are specified.
        """
        with self.assertRaises(CommandError):
            self.command.handle(all=False)

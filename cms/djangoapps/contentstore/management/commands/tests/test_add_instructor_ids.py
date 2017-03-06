"""
Unit test for add_instructor_ids management command.
"""
import mock

from django.core.management import call_command, CommandError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class TestAddInstructorID(ModuleStoreTestCase):
    """
    Test add_instructor_ids management command.
    """

    def setUp(self):
        super(TestAddInstructorID, self).setUp()

        self.org = 'TextX'
        self.course = CourseFactory.create(
            org=self.org,
            instructor_info={
                'instructors': [
                    {
                        'name': 'test-instructor1',
                        'organization': 'TextX',
                    },
                    {
                        'name': 'test-instructor2',
                        'organization': 'TextX',
                    }
                ]
            }
        )
        self.course_key = unicode(self.course.id)

        # Creating CourseOverview Object from course descriptor because
        # we are filtering the courses by organizations in CourseOverview.
        self.course_overview = CourseOverview.load_from_module_store(self.course.id)

    def assert_uuid_populated(self):
        """
        Checks UUID should be populated.
        """
        instructors = CourseDetails.fetch(CourseKey.from_string(self.course_key)).instructor_info
        for instructor in instructors.get("instructors", []):   # pylint: disable=E1101
            self.assertIn("uuid", instructor)

    def assert_uuid_not_populated(self):
        """
        Checks UUID should not be populated.
        """
        instructors = CourseDetails.fetch(CourseKey.from_string(self.course_key)).instructor_info
        for instructor in instructors.get("instructors", []):   # pylint: disable=E1101
            self.assertNotIn("uuid", instructor)

    def test_uuid_population_by_course_key(self):
        """
        Test population of instructor's uuid by course_keys.
        """
        call_command(
            "add_instructor_ids",
            "--username", self.user.username,
            "--course_keys", self.course_key
        )

        self.assert_uuid_populated()

    def test_uuid_population_by_org(self):
        """
        Test population of instructor's uuid by organizations.
        """
        # Mocked the raw_input and returns 'n'
        with mock.patch('__builtin__.raw_input', return_value='n') as _raw_input:
            call_command(
                "add_instructor_ids",
                "--username", self.user.username,
                "--orgs", self.org
            )

        self.assert_uuid_not_populated()

        # Mocked the raw_input and returns 'y'
        with mock.patch('__builtin__.raw_input', return_value='y') as _raw_input:
            call_command(
                "add_instructor_ids",
                "--username", self.user.username,
                "--orgs", self.org
            )

        self.assert_uuid_populated()

    def test_insufficient_args(self):
        """
        Test management command with insufficient arguments.
        """
        with self.assertRaises(CommandError):
            call_command(
                "add_instructor_ids",
                "--username", self.user.username,
            )

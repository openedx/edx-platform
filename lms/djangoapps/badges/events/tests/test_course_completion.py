"""
Tests for the course completion helper functions.
"""
from datetime import datetime

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from badges.events import course_complete


class CourseCompleteTestCase(ModuleStoreTestCase):
    """
    Tests for the course completion helper functions.
    """
    def setUp(self, **kwargs):
        super(CourseCompleteTestCase, self).setUp()
        # Need key to be deterministic to test slugs.
        self.course = CourseFactory.create(
            org='edX', course='course_test', run='test_run', display_name='Badged',
            start=datetime(year=2015, month=5, day=19),
            end=datetime(year=2015, month=5, day=20)
        )
        self.course_key = self.course.location.course_key

    def test_slug(self):
        """
        Verify slug generation is working as expected. If this test fails, the algorithm has changed, and it will cause
        the handler to lose track of all badges it made in the past.
        """
        self.assertEqual(
            course_complete.course_slug(self.course_key, 'honor'),
            'edxcourse_testtest_run_honor_fc5519b'
        )
        self.assertEqual(
            course_complete.course_slug(self.course_key, 'verified'),
            'edxcourse_testtest_run_verified_a199ec0'
        )

    def test_self_paced_description(self):
        """
        Verify that a badge created for a course with no end date gets a different description.
        """
        self.course.end = None
        self.assertEqual(
            course_complete.badge_description(self.course, 'honor'),
            'Completed the course "Badged" (honor)'
        )

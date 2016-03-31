"""
Tests for Verified Track Cohorting models
"""
from django.test import TestCase

from opaque_keys.edx.keys import CourseKey

from verified_track_content.models import VerifiedTrackCohortedCourse


class TestVerifiedTrackCohortedCourse(TestCase):
    """
    Tests that the configuration works as expected.
    """
    SAMPLE_COURSE = 'edX/Test_Course/Run'

    def test_course_enabled(self):
        course_key = CourseKey.from_string(self.SAMPLE_COURSE)
        # Test when no configuration exists
        self.assertFalse(VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(course_key))

        # Enable for a course
        config = VerifiedTrackCohortedCourse.objects.create(course_key=course_key, enabled=True)
        config.save()
        self.assertTrue(VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(course_key))

        # Disable for the course
        config.enabled = False
        config.save()
        self.assertFalse(VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(course_key))

    def test_unicode(self):
        course_key = CourseKey.from_string(self.SAMPLE_COURSE)
        # Enable for a course
        config = VerifiedTrackCohortedCourse.objects.create(course_key=course_key, enabled=True)
        config.save()
        self.assertEqual(unicode(config), "Course: {}, enabled: True".format(self.SAMPLE_COURSE))

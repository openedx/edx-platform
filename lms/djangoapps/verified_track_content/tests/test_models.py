"""
Tests for Verified Track Cohorting models
"""
from django.test import TestCase
import mock
from mock import patch

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.course_groups.cohorts import get_cohort
from student.models import CourseMode
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from verified_track_content.models import VerifiedTrackCohortedCourse
from verified_track_content.tasks import sync_cohort_with_mode, VERIFIED_COHORT_NAME
from openedx.core.djangoapps.course_groups.cohorts import (
    set_course_cohort_settings, add_cohort, CourseCohort, DEFAULT_COHORT_NAME
)


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


class TestMoveToVerified(SharedModuleStoreTestCase):
    """ Tests for the post-save listener. """

    @classmethod
    def setUpClass(cls):
        super(TestMoveToVerified, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        self.user = UserFactory()
        # Spy on number of calls to celery task.
        celery_task_patcher = patch.object(
            sync_cohort_with_mode, 'apply_async',
            mock.Mock(wraps=sync_cohort_with_mode.apply_async)
        )
        self.mocked_celery_task = celery_task_patcher.start()
        self.addCleanup(celery_task_patcher.stop)

    def _enable_cohorting(self):
        set_course_cohort_settings(self.course.id, is_cohorted=True)

    def _create_verified_cohort(self):
        add_cohort(self.course.id, VERIFIED_COHORT_NAME, CourseCohort.MANUAL)

    def _enable_verified_track_cohorting(self):
        """ Enable verified track cohorting for the default course. """
        config = VerifiedTrackCohortedCourse.objects.create(course_key=self.course.id, enabled=True)
        config.save()

    def _enroll_in_course(self):
        self.enrollment = CourseEnrollmentFactory(course_id=self.course.id, user=self.user)

    def _upgrade_to_verified(self):
        """ Upgrade the default enrollment to verified. """
        self.enrollment.update_enrollment(mode=CourseMode.VERIFIED)

    def _verify_no_automatic_cohorting(self):
        self._enroll_in_course()
        self.assertIsNone(get_cohort(self.user, self.course.id, assign=False))
        self._upgrade_to_verified()
        self.assertIsNone(get_cohort(self.user, self.course.id, assign=False))
        self.assertEqual(0, self.mocked_celery_task.call_count)

    def _unenroll(self):
        self.enrollment.unenroll(self.user, self.course.id)

    def _reenroll(self):
        self.enrollment.activate()
        self.enrollment.change_mode(CourseMode.AUDIT)

    @mock.patch('verified_track_content.models.log.error')
    def test_automatic_cohorting_disabled(self, error_logger):
        """
        If the VerifiedTrackCohortedCourse feature is disabled for a course, enrollment mode changes do not move
        learners into a cohort.
        """
        # Enable cohorting and create a verified cohort.
        self._enable_cohorting()
        self._create_verified_cohort()
        # But do not enable the verified track cohorting feature.
        self.assertFalse(VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(self.course.id))
        self._verify_no_automatic_cohorting()
        # No logging occurs if feature is disabled for course.
        self.assertFalse(error_logger.called)

    @mock.patch('verified_track_content.models.log.error')
    def test_cohorting_enabled_course_not_cohorted(self, error_logger):
        """
        If the VerifiedTrackCohortedCourse feature is enabled for a course, but the course is not cohorted,
        an error is logged and enrollment mode changes do not move learners into a cohort.
        """
        # Enable verified track cohorting feature, but course has not been marked as cohorting.
        self._enable_verified_track_cohorting()
        self.assertTrue(VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(self.course.id))
        self._verify_no_automatic_cohorting()
        self.assertTrue(error_logger.called)
        self.assertIn("course is not cohorted", error_logger.call_args[0][0])

    @mock.patch('verified_track_content.models.log.error')
    def test_cohorting_enabled_missing_verified_cohort(self, error_logger):
        """
        If the VerifiedTrackCohortedCourse feature is enabled for a course and the course is cohorted,
        but the course does not have a verified cohort, an error is logged and enrollment mode changes do not
        move learners into a cohort.
        """
        # Enable cohorting, but do not create the verified cohort.
        self._enable_cohorting()
        # Enable verified track cohorting feature
        self._enable_verified_track_cohorting()
        self.assertTrue(VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(self.course.id))
        self._verify_no_automatic_cohorting()
        self.assertTrue(error_logger.called)
        self.assertIn("course does not have a verified cohort", error_logger.call_args[0][0])

    def test_automatic_cohorting_enabled(self):
        """
        If the VerifiedTrackCohortedCourse feature is enabled for a course (with course cohorting enabled
        with an existing verified cohort), enrollment in the verified track automatically moves learners
        into the verified cohort.
        """
        # Enable cohorting and create a verified cohort.
        self._enable_cohorting()
        self._create_verified_cohort()
        # Enable verified track cohorting feature
        self._enable_verified_track_cohorting()
        self.assertTrue(VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(self.course.id))
        self._enroll_in_course()

        self.assertEqual(2, self.mocked_celery_task.call_count)
        self.assertEqual(DEFAULT_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)

        self._upgrade_to_verified()
        self.assertEqual(4, self.mocked_celery_task.call_count)
        self.assertEqual(VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)

    def test_unenrolled(self):
        """
        Test that un-enrolling and re-enrolling works correctly. This is important because usually
        learners maintain their previously assigned cohort on re-enrollment.
        """
        # Enable verified track cohorting feature and enroll in the verified track
        self._enable_cohorting()
        self._create_verified_cohort()
        self._enable_verified_track_cohorting()
        self._enroll_in_course()
        self._upgrade_to_verified()
        self.assertEqual(VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)

        # Un-enroll from the course and then re-enroll
        self._unenroll()
        self.assertEqual(VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)
        self._reenroll()
        self.assertEqual(DEFAULT_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)
        self._upgrade_to_verified()
        self.assertEqual(VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)

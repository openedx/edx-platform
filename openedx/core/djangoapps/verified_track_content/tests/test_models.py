"""
Tests for Verified Track Cohorting models
"""
# pylint: disable=attribute-defined-outside-init
# pylint: disable=no-member

from django.test import TestCase
import mock
from mock import patch

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.course_groups.cohorts import get_cohort
from student.models import CourseMode
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from ..models import VerifiedTrackCohortedCourse, DEFAULT_VERIFIED_COHORT_NAME
from ..tasks import sync_cohort_with_mode
from openedx.core.djangoapps.course_groups.cohorts import (
    set_course_cohort_settings, add_cohort, CourseCohort, DEFAULT_COHORT_NAME
)
from openedx.core.djangolib.testing.utils import skip_unless_lms


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

    def test_verified_cohort_name(self):
        cohort_name = 'verified cohort'
        course_key = CourseKey.from_string(self.SAMPLE_COURSE)
        config = VerifiedTrackCohortedCourse.objects.create(
            course_key=course_key, enabled=True, verified_cohort_name=cohort_name
        )
        config.save()
        self.assertEqual(VerifiedTrackCohortedCourse.verified_cohort_name_for_course(course_key), cohort_name)

    def test_unset_verified_cohort_name(self):
        fake_course_id = 'fake/course/key'
        course_key = CourseKey.from_string(fake_course_id)
        self.assertEqual(VerifiedTrackCohortedCourse.verified_cohort_name_for_course(course_key), None)


@skip_unless_lms
class TestMoveToVerified(SharedModuleStoreTestCase):
    """ Tests for the post-save listener. """

    @classmethod
    def setUpClass(cls):
        super(TestMoveToVerified, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestMoveToVerified, self).setUp()
        self.user = UserFactory()
        # Spy on number of calls to celery task.
        celery_task_patcher = patch.object(
            sync_cohort_with_mode, 'apply_async',
            mock.Mock(wraps=sync_cohort_with_mode.apply_async)
        )
        self.mocked_celery_task = celery_task_patcher.start()
        self.addCleanup(celery_task_patcher.stop)

    def _enable_cohorting(self):
        """ Turn on cohorting in the course. """
        set_course_cohort_settings(self.course.id, is_cohorted=True)

    def _create_verified_cohort(self, name=DEFAULT_VERIFIED_COHORT_NAME):
        """ Create a verified cohort. """
        add_cohort(self.course.id, name, CourseCohort.MANUAL)

    def _create_named_random_cohort(self, name):
        """ Create a random cohort with the supplied name. """
        return add_cohort(self.course.id, name, CourseCohort.RANDOM)

    def _enable_verified_track_cohorting(self, cohort_name=None):
        """ Enable verified track cohorting for the default course. """
        if cohort_name:
            config = VerifiedTrackCohortedCourse.objects.create(
                course_key=self.course.id, enabled=True, verified_cohort_name=cohort_name
            )
        else:
            config = VerifiedTrackCohortedCourse.objects.create(course_key=self.course.id, enabled=True)
        config.save()

    def _enroll_in_course(self):
        """ Enroll self.user in self.course. """
        self.enrollment = CourseEnrollmentFactory(course_id=self.course.id, user=self.user)

    def _upgrade_to_verified(self):
        """ Upgrade the default enrollment to verified. """
        self.enrollment.update_enrollment(mode=CourseMode.VERIFIED)

    def _verify_no_automatic_cohorting(self):
        """ Check that upgrading self.user to verified does not move them into a cohort. """
        self._enroll_in_course()
        self.assertIsNone(get_cohort(self.user, self.course.id, assign=False))
        self._upgrade_to_verified()
        self.assertIsNone(get_cohort(self.user, self.course.id, assign=False))
        self.assertEqual(0, self.mocked_celery_task.call_count)

    def _unenroll(self):
        """ Unenroll self.user from self.course. """
        self.enrollment.unenroll(self.user, self.course.id)

    def _reenroll(self):
        """ Re-enroll the learner into mode AUDIT. """
        self.enrollment.activate()
        self.enrollment.change_mode(CourseMode.AUDIT)

    @mock.patch('openedx.core.djangoapps.verified_track_content.models.log.error')
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

    @mock.patch('openedx.core.djangoapps.verified_track_content.models.log.error')
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

    @mock.patch('openedx.core.djangoapps.verified_track_content.models.log.error')
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
        error_message = "cohort named '%s' does not exist"
        self.assertIn(error_message, error_logger.call_args[0][0])

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
        self.assertEqual(DEFAULT_VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)

    def test_cohorting_enabled_multiple_random_cohorts(self):
        """
        If the VerifiedTrackCohortedCourse feature is enabled for a course, and the course is cohorted
        with > 1 random cohorts, the learner is randomly assigned to one of the random
        cohorts when in the audit track.
        """
        # Enable cohorting, and create the verified cohort.
        self._enable_cohorting()
        self._create_verified_cohort()
        # Create two random cohorts.
        self._create_named_random_cohort("Random 1")
        self._create_named_random_cohort("Random 2")
        # Enable verified track cohorting feature
        self._enable_verified_track_cohorting()

        self._enroll_in_course()
        self.assertIn(get_cohort(self.user, self.course.id, assign=False).name, ["Random 1", "Random 2"])
        self._upgrade_to_verified()
        self.assertEqual(DEFAULT_VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)

        self._unenroll()
        self._reenroll()
        self.assertIn(get_cohort(self.user, self.course.id, assign=False).name, ["Random 1", "Random 2"])

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
        self.assertEqual(DEFAULT_VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)

        # Un-enroll from the course and then re-enroll
        self._unenroll()
        self.assertEqual(DEFAULT_VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)
        self._reenroll()
        self.assertEqual(DEFAULT_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)
        self._upgrade_to_verified()
        self.assertEqual(DEFAULT_VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)

    def test_custom_verified_cohort_name(self):
        """
        Test that enrolling in verified works correctly when the "verified cohort" has a custom name.
        """
        custom_cohort_name = 'special verified cohort'
        self._enable_cohorting()
        self._create_verified_cohort(name=custom_cohort_name)
        self._enable_verified_track_cohorting(cohort_name=custom_cohort_name)
        self._enroll_in_course()
        self._upgrade_to_verified()
        self.assertEqual(custom_cohort_name, get_cohort(self.user, self.course.id, assign=False).name)

    def test_custom_default_cohort_name(self):
        """
        Test that enrolling and un-enrolling works correctly when the single cohort
        of type random has a different name from "Default Group".
        """
        random_cohort_name = "custom random cohort"
        self._enable_cohorting()
        self._create_verified_cohort()
        default_cohort = self._create_named_random_cohort(random_cohort_name)
        self._enable_verified_track_cohorting()
        self._enroll_in_course()
        self.assertEqual(random_cohort_name, get_cohort(self.user, self.course.id, assign=False).name)
        self._upgrade_to_verified()
        self.assertEqual(DEFAULT_VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)

        # Un-enroll from the course. The learner stays in the verified cohort, but is no longer active.
        self._unenroll()
        self.assertEqual(DEFAULT_VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)

        # Change the name of the "default" cohort.
        modified_cohort_name = "renamed random cohort"
        default_cohort.name = modified_cohort_name
        default_cohort.save()

        # Re-enroll in the course, which will downgrade the learner to audit.
        self._reenroll()
        self.assertEqual(modified_cohort_name, get_cohort(self.user, self.course.id, assign=False).name)
        self._upgrade_to_verified()
        self.assertEqual(DEFAULT_VERIFIED_COHORT_NAME, get_cohort(self.user, self.course.id, assign=False).name)

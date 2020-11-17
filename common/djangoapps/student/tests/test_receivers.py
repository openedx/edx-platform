""" Tests for student signal receivers. """

from edx_toggles.toggles.testutils import override_waffle_flag
from lms.djangoapps.courseware.toggles import (
    COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES,
    COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES_FIRST_SECTION_CELEBRATION,
    REDIRECT_TO_COURSEWARE_MICROFRONTEND
)
from lms.djangoapps.experiments.testutils import override_experiment_waffle_flag
from common.djangoapps.student.models import CourseEnrollmentCelebration
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase


class ReceiversTest(SharedModuleStoreTestCase):
    """
    Tests for dashboard utility functions
    """
    @override_experiment_waffle_flag(REDIRECT_TO_COURSEWARE_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES, active=True)
    @override_waffle_flag(COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES_FIRST_SECTION_CELEBRATION, active=True)
    def test_celebration_created(self):
        """ Test that we make celebration objects when enrollments are created """
        self.assertEqual(CourseEnrollmentCelebration.objects.count(), 0)

        # Test initial creation upon an enrollment being made
        enrollment = CourseEnrollmentFactory()
        self.assertEqual(CourseEnrollmentCelebration.objects.count(), 1)
        celebration = CourseEnrollmentCelebration.objects.get(enrollment=enrollment, celebrate_first_section=True)

        # Test nothing changes if we update that enrollment
        celebration.celebrate_first_section = False
        celebration.save()
        enrollment.mode = 'test-mode'
        enrollment.save()
        self.assertEqual(CourseEnrollmentCelebration.objects.count(), 1)
        CourseEnrollmentCelebration.objects.get(enrollment=enrollment, celebrate_first_section=False)

    def test_celebration_gated_by_waffle(self):
        """ Test we don't make a celebration if the MFE redirect waffle flag is off """
        CourseEnrollmentFactory()
        self.assertEqual(CourseEnrollmentCelebration.objects.count(), 0)

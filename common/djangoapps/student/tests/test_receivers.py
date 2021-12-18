""" Tests for student signal receivers. """

from edx_name_affirmation.signals import VERIFIED_NAME_APPROVED
from edx_toggles.toggles.testutils import override_waffle_flag
from lms.djangoapps.courseware.toggles import COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES
from common.djangoapps.student.models import (
    CourseEnrollmentCelebration,
    PendingNameChange,
    UserProfile
)
from common.djangoapps.student.tests.factories import (
    CourseEnrollmentFactory,
    UserFactory,
    UserProfileFactory
)
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order


class ReceiversTest(SharedModuleStoreTestCase):
    """
    Tests for dashboard utility functions
    """
    @override_waffle_flag(COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES, active=True)
    def test_celebration_created(self):
        """ Test that we make celebration objects when enrollments are created """
        assert CourseEnrollmentCelebration.objects.count() == 0

        # Test initial creation upon an enrollment being made
        enrollment = CourseEnrollmentFactory()
        assert CourseEnrollmentCelebration.objects.count() == 1
        celebration = CourseEnrollmentCelebration.objects.get(enrollment=enrollment, celebrate_first_section=True)

        # Test nothing changes if we update that enrollment
        celebration.celebrate_first_section = False
        celebration.save()
        enrollment.mode = 'test-mode'
        enrollment.save()
        assert CourseEnrollmentCelebration.objects.count() == 1
        CourseEnrollmentCelebration.objects.get(enrollment=enrollment, celebrate_first_section=False)

    def test_celebration_gated_by_waffle(self):
        """ Test we don't make a celebration if the MFE redirect waffle flag is off """
        CourseEnrollmentFactory()
        assert CourseEnrollmentCelebration.objects.count() == 0

    def test_listen_for_verified_name_approved(self):
        """
        Test that profile name is updated when a pending name change is approved
        """
        user = UserFactory(email='email@test.com', username='jdoe')
        UserProfileFactory(user=user)

        new_name = 'John Doe'
        PendingNameChange.objects.create(user=user, new_name=new_name)
        assert PendingNameChange.objects.count() == 1

        # Send a VERIFIED_NAME_APPROVED signal where the profile name matches the name
        # change request
        VERIFIED_NAME_APPROVED.send(sender=None, user_id=user.id, profile_name=new_name)

        # Assert that the pending name change was deleted and the profile name was updated
        assert PendingNameChange.objects.count() == 0
        profile = UserProfile.objects.get(user=user)
        assert profile.name == new_name

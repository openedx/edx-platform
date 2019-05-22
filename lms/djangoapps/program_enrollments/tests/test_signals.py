"""
Test signal handlers for program_enrollments
"""

from __future__ import absolute_import

from lms.djangoapps.program_enrollments.api.v1.tests.factories import ProgramEnrollmentFactory
from lms.djangoapps.program_enrollments.signals import _listen_for_lms_retire
from openedx.core.djangoapps.user_api.accounts.tests.retirement_helpers import fake_completed_retirement
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class ProgramEnrollmentRetireSignalTests(ModuleStoreTestCase):
    """
    Test the _listen_for_lms_retire signal
    """

    def create_enrollment_and_history(self, user=None):
        """
        Create ProgramEnrollment and several History entries
        """
        if user:
            enrollment = ProgramEnrollmentFactory(user=user)
        else:
            enrollment = ProgramEnrollmentFactory()
        for status in ['pending', 'suspended', 'withdrawn', 'enrolled']:
            enrollment.status = status
            enrollment.save()
        return enrollment

    def assert_enrollment_and_history_retired(self, enrollment):
        """
        Assert that for the enrollment and all histories, external key is None
        """
        enrollment.refresh_from_db()
        self.assertIsNone(enrollment.external_user_key)
        for history_record in enrollment.historical_records.all():
            self.assertIsNone(history_record.external_user_key)

    def test_retire_enrollment(self):
        """
        Test basic retirement of program enrollment
        """
        enrollment = self.create_enrollment_and_history()
        _listen_for_lms_retire(sender=self.__class__, user=enrollment.user)
        self.assert_enrollment_and_history_retired(enrollment)

    def test_retire_enrollment_multiple(self):
        """
        Test basic retirement of user with multiple program enrollments
        """
        enrollment = self.create_enrollment_and_history()
        enrollment2 = self.create_enrollment_and_history(user=enrollment.user)
        enrollment3 = self.create_enrollment_and_history(user=enrollment.user)
        _listen_for_lms_retire(sender=self.__class__, user=enrollment.user)
        self.assert_enrollment_and_history_retired(enrollment)
        self.assert_enrollment_and_history_retired(enrollment2)
        self.assert_enrollment_and_history_retired(enrollment3)

    def test_success_no_enrollment(self):
        """
        Basic success path for users who have no enrollments, should simply not error
        """
        user = UserFactory()
        _listen_for_lms_retire(sender=self.__class__, user=user)

    def test_idempotent(self):
        """
        Tests that running a retirement multiple times does not throw an error
        """
        enrollment = self.create_enrollment_and_history()

        # Run twice to make sure no errors are raised
        _listen_for_lms_retire(sender=self.__class__, user=enrollment.user)
        fake_completed_retirement(enrollment.user)
        _listen_for_lms_retire(sender=self.__class__, user=enrollment.user)

        self.assert_enrollment_and_history_retired(enrollment)

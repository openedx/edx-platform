"""Tests for per-course verification status on the dashboard. """
from datetime import datetime, timedelta

import ddt
from mock import patch
from pytz import UTC
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.conf import settings

from student.helpers import (
    VERIFY_STATUS_NEED_TO_VERIFY,
    VERIFY_STATUS_SUBMITTED,
    VERIFY_STATUS_APPROVED,
    VERIFY_STATUS_MISSED_DEADLINE
)

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, mixed_store_config
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from course_modes.tests.factories import CourseModeFactory
from verify_student.models import SoftwareSecurePhotoVerification


MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
@patch.dict(settings.FEATURES, {
    'SEPARATE_VERIFICATION_FROM_PAYMENT': True,
    'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True
})
@ddt.ddt
class TestCourseVerificationStatus(ModuleStoreTestCase):
    """Tests for per-course verification status on the dashboard. """

    PAST = datetime.now(UTC) - timedelta(days=5)
    FUTURE = datetime.now(UTC) + timedelta(days=5)

    def setUp(self):
        self.user = UserFactory(password="edx")
        self.course = CourseFactory.create()
        success = self.client.login(username=self.user.username, password="edx")
        self.assertTrue(success, msg="Did not log in successfully")

    def test_enrolled_as_non_verified(self):
        self._setup_mode_and_enrollment(None, "honor")

        # Expect that the course appears on the dashboard
        # without any verification messaging
        self._assert_course_verification_status(None)

    def test_no_verified_mode_available(self):
        # Enroll the student in a verified mode, but don't
        # create any verified course mode.
        # This won't happen unless someone deletes a course mode,
        # but if so, make sure we handle it gracefully.
        CourseEnrollmentFactory(
            course_id=self.course.id,
            user=self.user,
            mode="verified"
        )

        # The default course has no verified mode,
        # so no verification status should be displayed
        self._assert_course_verification_status(None)

    @ddt.data(None, FUTURE)
    def test_need_to_verify(self, expiration):
        self._setup_mode_and_enrollment(expiration, "verified")

        # Since the student has not submitted a photo verification,
        # the student should see a "need to verify" message
        self._assert_course_verification_status(VERIFY_STATUS_NEED_TO_VERIFY)

        # Start the photo verification process, but do not submit
        # Since we haven't submitted the verification, we should still
        # see the "need to verify" message
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        self._assert_course_verification_status(VERIFY_STATUS_NEED_TO_VERIFY)

        # Upload images, but don't submit to the verification service
        # We should still need to verify
        attempt.mark_ready()
        self._assert_course_verification_status(VERIFY_STATUS_NEED_TO_VERIFY)

    @ddt.data(None, FUTURE)
    def test_waiting_approval(self, expiration):
        self._setup_mode_and_enrollment(expiration, "verified")

        # The student has submitted a photo verification
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()

        # Now the student should see a "verification submitted" message
        self._assert_course_verification_status(VERIFY_STATUS_SUBMITTED)

    @ddt.data(None, FUTURE)
    def test_fully_verified(self, expiration):
        self._setup_mode_and_enrollment(expiration, "verified")

        # The student has an approved verification
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()
        attempt.approve()

        # Expect that the successfully verified message is shown
        self._assert_course_verification_status(VERIFY_STATUS_APPROVED)

    def test_missed_verification_deadline(self):
        # Expiration date in the past
        self._setup_mode_and_enrollment(self.PAST, "verified")

        # The student does NOT have an approved verification
        # so the status should show that the student missed the deadline.
        self._assert_course_verification_status(VERIFY_STATUS_MISSED_DEADLINE)

    def test_missed_verification_deadline_verification_was_expired(self):
        # Expiration date in the past
        self._setup_mode_and_enrollment(self.PAST, "verified")

        # Create a verification, but the expiration date of the verification
        # occurred before the deadline.
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()
        attempt.approve()
        attempt.created_at = self.PAST - timedelta(days=900)
        attempt.save()

        # The student didn't have an approved verification at the deadline,
        # so we should show that the student missed the deadline.
        self._assert_course_verification_status(VERIFY_STATUS_MISSED_DEADLINE)

    def test_missed_verification_deadline_but_later_verified(self):
        # Expiration date in the past
        self._setup_mode_and_enrollment(self.PAST, "verified")

        # Successfully verify, but after the deadline has already passed
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()
        attempt.approve()
        attempt.created_at = self.PAST - timedelta(days=900)
        attempt.save()

        # The student didn't have an approved verification at the deadline,
        # so we should show that the student missed the deadline.
        self._assert_course_verification_status(VERIFY_STATUS_MISSED_DEADLINE)

    def test_verification_denied(self):
        # Expiration date in the future
        self._setup_mode_and_enrollment(self.FUTURE, "verified")

        # Create a verification with the specified status
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()
        attempt.deny("Not valid!")

        # Since this is not a status we handle, don't display any
        # messaging relating to verification
        self._assert_course_verification_status(None)

    def test_verification_error(self):
        # Expiration date in the future
        self._setup_mode_and_enrollment(self.FUTURE, "verified")

        # Create a verification with the specified status
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.status = "must_retry"
        attempt.system_error("Error!")

        # Since this is not a status we handle, don't display any
        # messaging relating to verification
        self._assert_course_verification_status(None)

    def _setup_mode_and_enrollment(self, deadline, enrollment_mode):
        """Create a course mode and enrollment.

        Arguments:
            deadline (datetime): The deadline for submitting your verification.
            enrollment_mode (str): The mode of the enrollment.

        """
        CourseModeFactory(
            course_id=self.course.id,
            mode_slug="verified",
            expiration_datetime=deadline
        )
        CourseEnrollmentFactory(
            course_id=self.course.id,
            user=self.user,
            mode=enrollment_mode
        )

    BANNER_ALT_MESSAGES = {
        None: "Honor",
        VERIFY_STATUS_NEED_TO_VERIFY: "ID Verified Pending Ribbon/Badge",
        VERIFY_STATUS_SUBMITTED: "ID Verified Pending Ribbon/Badge",
        VERIFY_STATUS_APPROVED: "ID Verified Ribbon/Badge",

        # TODO: do we want to display honor code instead?
        VERIFY_STATUS_MISSED_DEADLINE: "ID Verified Pending Ribbon/Badge"
    }

    NOTIFICATION_MESSAGES = {
        VERIFY_STATUS_NEED_TO_VERIFY: "You still need to verify for this course.",
        VERIFY_STATUS_SUBMITTED: "You have already verified your ID!",
        VERIFY_STATUS_MISSED_DEADLINE: "You did not submit your verification before the deadline."
    }

    def _assert_course_verification_status(self, status):
        """Check whether the specified verification status is shown on the dashboard.

        Arguments:
            status (str): One of the verification status constants.
                If None, check that *none* of the statuses are displayed.

        Raises:
            AssertionError

        """
        response = self.client.get(reverse('dashboard'))

        # Sanity check: verify that the course is on the page
        self.assertContains(response, unicode(self.course.id))

        # Verify that the correct banner is rendered on the dashboard
        self.assertContains(response, self.BANNER_ALT_MESSAGES[status])

        # Verify that the correct copy is rendered on the dashboard
        # (and no other copy is also rendered!)
        for msg_status, msg in self.NOTIFICATION_MESSAGES.iteritems():
            if msg_status == status:
                self.assertContains(response, msg)
            else:
                self.assertNotContains(response, msg)

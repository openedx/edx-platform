"""Tests for per-course verification status on the dashboard. """
from datetime import datetime, timedelta

import unittest
import ddt
from mock import patch
from pytz import UTC
from django.core.urlresolvers import reverse
from django.conf import settings

from student.helpers import (
    VERIFY_STATUS_NEED_TO_VERIFY,
    VERIFY_STATUS_SUBMITTED,
    VERIFY_STATUS_APPROVED,
    VERIFY_STATUS_MISSED_DEADLINE,
    VERIFY_STATUS_NEED_TO_REVERIFY
)

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.verify_student.models import VerificationDeadline, SoftwareSecurePhotoVerification
from util.testing import UrlResetMixin


@patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@ddt.ddt
class TestCourseVerificationStatus(UrlResetMixin, ModuleStoreTestCase):
    """Tests for per-course verification status on the dashboard. """

    PAST = datetime.now(UTC) - timedelta(days=5)
    FUTURE = datetime.now(UTC) + timedelta(days=5)

    def setUp(self):
        # Invoke UrlResetMixin
        super(TestCourseVerificationStatus, self).setUp('verify_student.urls')

        self.user = UserFactory(password="edx")
        self.course = CourseFactory.create()
        success = self.client.login(username=self.user.username, password="edx")
        self.assertTrue(success, msg="Did not log in successfully")
        self.dashboard_url = reverse('dashboard')

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

        # Continue to show the student as needing to verify.
        # The student is enrolled as verified, so we might as well let them
        # complete verification.  We'd need to change their enrollment mode
        # anyway to ensure that the student is issued the correct kind of certificate.
        self._assert_course_verification_status(VERIFY_STATUS_NEED_TO_VERIFY)

    def test_need_to_verify_no_expiration(self):
        self._setup_mode_and_enrollment(None, "verified")

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

    def test_need_to_verify_expiration(self):
        self._setup_mode_and_enrollment(self.FUTURE, "verified")
        response = self.client.get(self.dashboard_url)
        self.assertContains(response, self.BANNER_ALT_MESSAGES[VERIFY_STATUS_NEED_TO_VERIFY])
        self.assertContains(response, "You only have 4 days left to verify for this course.")

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

        # Check that the "verification good until" date is displayed
        response = self.client.get(self.dashboard_url)
        self.assertContains(response, attempt.expiration_datetime.strftime("%m/%d/%Y"))

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

    def test_verification_will_expire_by_deadline(self):
        # Expiration date in the future
        self._setup_mode_and_enrollment(self.FUTURE, "verified")

        # Create a verification attempt that:
        # 1) Is current (submitted in the last year)
        # 2) Will expire by the deadline for the course
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()

        # This attempt will expire tomorrow, before the course deadline
        attempt.created_at = attempt.created_at - timedelta(days=364)
        attempt.save()

        # Expect that the "verify now" message is hidden
        # (since the user isn't allowed to submit another attempt while
        # a verification is active).
        self._assert_course_verification_status(VERIFY_STATUS_NEED_TO_REVERIFY)

    def test_verification_occurred_after_deadline(self):
        # Expiration date in the past
        self._setup_mode_and_enrollment(self.PAST, "verified")

        # The deadline has passed, and we've asked the student
        # to reverify (through the support team).
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()

        # Expect that the user's displayed enrollment mode is verified.
        self._assert_course_verification_status(VERIFY_STATUS_APPROVED)

    def test_with_two_verifications(self):
        # checking if a user has two verification and but most recent verification course deadline is expired

        self._setup_mode_and_enrollment(self.FUTURE, "verified")

        # The student has an approved verification
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()
        attempt.approve()
        # Making created at to previous date to differentiate with 2nd attempt.
        attempt.created_at = datetime.now(UTC) - timedelta(days=1)
        attempt.save()

        # Expect that the successfully verified message is shown
        self._assert_course_verification_status(VERIFY_STATUS_APPROVED)

        # Check that the "verification good until" date is displayed
        response = self.client.get(self.dashboard_url)
        self.assertContains(response, attempt.expiration_datetime.strftime("%m/%d/%Y"))

        # Adding another verification with different course.
        # Its created_at is greater than course deadline.
        course2 = CourseFactory.create()
        CourseModeFactory(
            course_id=course2.id,
            mode_slug="verified",
            expiration_datetime=self.PAST
        )
        CourseEnrollmentFactory(
            course_id=course2.id,
            user=self.user,
            mode="verified"
        )

        # The student has an approved verification
        attempt2 = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt2.mark_ready()
        attempt2.submit()
        attempt2.approve()
        attempt2.save()

        # Mark the attemp2 as approved so its date will appear on dasboard.
        self._assert_course_verification_status(VERIFY_STATUS_APPROVED)
        response2 = self.client.get(self.dashboard_url)
        self.assertContains(response2, attempt2.expiration_datetime.strftime("%m/%d/%Y"))
        self.assertEqual(response2.content.count(attempt2.expiration_datetime.strftime("%m/%d/%Y")), 2)

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
        VerificationDeadline.set_deadline(self.course.id, deadline)

    BANNER_ALT_MESSAGES = {
        None: "Honor",
        VERIFY_STATUS_NEED_TO_VERIFY: "ID verification pending",
        VERIFY_STATUS_SUBMITTED: "ID verification pending",
        VERIFY_STATUS_APPROVED: "ID Verified Ribbon/Badge",
        VERIFY_STATUS_MISSED_DEADLINE: "Honor",
        VERIFY_STATUS_NEED_TO_REVERIFY: "Honor"
    }

    NOTIFICATION_MESSAGES = {
        VERIFY_STATUS_NEED_TO_VERIFY: [
            "You still need to verify for this course.",
            "Verification not yet complete"
        ],
        VERIFY_STATUS_SUBMITTED: ["Thanks for your patience as we process your request."],
        VERIFY_STATUS_APPROVED: ["You have already verified your ID!"],
        VERIFY_STATUS_NEED_TO_REVERIFY: ["Your verification will expire soon!"]
    }

    MODE_CLASSES = {
        None: "honor",
        VERIFY_STATUS_NEED_TO_VERIFY: "verified",
        VERIFY_STATUS_SUBMITTED: "verified",
        VERIFY_STATUS_APPROVED: "verified",
        VERIFY_STATUS_MISSED_DEADLINE: "honor",
        VERIFY_STATUS_NEED_TO_REVERIFY: "honor"
    }

    def _assert_course_verification_status(self, status):
        """Check whether the specified verification status is shown on the dashboard.

        Arguments:
            status (str): One of the verification status constants.
                If None, check that *none* of the statuses are displayed.

        Raises:
            AssertionError

        """
        response = self.client.get(self.dashboard_url)

        # Sanity check: verify that the course is on the page
        self.assertContains(response, unicode(self.course.id))

        # Verify that the correct banner is rendered on the dashboard
        self.assertContains(response, self.BANNER_ALT_MESSAGES[status])

        # Verify that the correct banner color is rendered
        self.assertContains(
            response,
            "<article class=\"course {}\">".format(self.MODE_CLASSES[status])
        )

        # Verify that the correct copy is rendered on the dashboard
        if status is not None:
            if status in self.NOTIFICATION_MESSAGES:
                # Different states might have different messaging
                # so in some cases we check several possibilities
                # and fail if none of these are found.
                found_msg = False
                for message in self.NOTIFICATION_MESSAGES[status]:
                    if message in response.content:
                        found_msg = True
                        break

                fail_msg = "Could not find any of these messages: {expected}".format(
                    expected=self.NOTIFICATION_MESSAGES[status]
                )
                self.assertTrue(found_msg, msg=fail_msg)
        else:
            # Combine all possible messages into a single list
            all_messages = []
            for msg_group in self.NOTIFICATION_MESSAGES.values():
                all_messages.extend(msg_group)

            # Verify that none of the messages are displayed
            for msg in all_messages:
                self.assertNotContains(response, msg)

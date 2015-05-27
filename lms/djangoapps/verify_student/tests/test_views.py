# encoding: utf-8
"""
Tests of verify_student views.
"""
import json
import urllib
from datetime import timedelta, datetime
from uuid import uuid4

from django.test.utils import override_settings
import mock
from mock import patch, Mock
import pytz
import ddt
from django.test.client import Client
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core import mail
from bs4 import BeautifulSoup
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.locator import CourseLocator

from openedx.core.djangoapps.user_api.accounts.api import get_account_settings
from commerce.exceptions import ApiError
from commerce.tests import EcommerceApiTestMixin
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from student.models import CourseEnrollment
from course_modes.tests.factories import CourseModeFactory
from course_modes.models import CourseMode
from shoppingcart.models import Order, CertificateItem
from embargo.test_utils import restrict_course
from util.testing import UrlResetMixin
from verify_student.views import (
    render_to_response, PayAndVerifyView, EVENT_NAME_USER_ENTERED_INCOURSE_REVERIFY_VIEW,
    EVENT_NAME_USER_SUBMITTED_INCOURSE_REVERIFY
)
from verify_student.models import (
    SoftwareSecurePhotoVerification, VerificationCheckpoint,
    InCourseReverificationConfiguration
)
from reverification.tests.factories import MidcourseReverificationWindowFactory


def mock_render_to_response(*args, **kwargs):
    return render_to_response(*args, **kwargs)

render_mock = Mock(side_effect=mock_render_to_response)


class StartView(TestCase):
    def start_url(self, course_id=""):
        return "/verify_student/{0}".format(urllib.quote(course_id))

    def test_start_new_verification(self):
        """
        Test the case where the user has no pending `PhotoVerificationAttempts`,
        but is just starting their first.
        """
        user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")

    def must_be_logged_in(self):
        self.assertHttpForbidden(self.client.get(self.start_url()))


@ddt.ddt
class TestPayAndVerifyView(UrlResetMixin, ModuleStoreTestCase):
    """
    Tests for the payment and verification flow views.
    """
    MIN_PRICE = 12
    USERNAME = "test_user"
    PASSWORD = "test_password"

    NOW = datetime.now(pytz.UTC)
    YESTERDAY = NOW - timedelta(days=1)
    TOMORROW = NOW + timedelta(days=1)

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        super(TestPayAndVerifyView, self).setUp('embargo')
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result, msg="Could not log in")

    @ddt.data("verified", "professional")
    def test_start_flow_not_verified(self, course_mode):
        course = self._create_course(course_mode)
        self._enroll(course.id, "honor")
        response = self._get_page('verify_student_start_flow', course.id)
        self._assert_displayed_mode(response, course_mode)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS + PayAndVerifyView.VERIFICATION_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_messaging(response, PayAndVerifyView.FIRST_TIME_VERIFY_MSG)
        self._assert_requirements_displayed(response, [
            PayAndVerifyView.PHOTO_ID_REQ,
            PayAndVerifyView.WEBCAM_REQ,
        ])
        self._assert_upgrade_session_flag(False)

    @ddt.data("no-id-professional")
    def test_start_flow_with_no_id_professional(self, course_mode):
        course = self._create_course(course_mode)
        # by default enrollment is honor
        self._enroll(course.id, "honor")
        response = self._get_page('verify_student_start_flow', course.id)
        self._assert_displayed_mode(response, course_mode)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_messaging(response, PayAndVerifyView.FIRST_TIME_VERIFY_MSG)
        self._assert_requirements_displayed(response, [])

    @ddt.data("expired", "denied")
    def test_start_flow_expired_or_denied_verification(self, verification_status):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        self._set_verification_status(verification_status)
        response = self._get_page('verify_student_start_flow', course.id)

        # Expect the same content as when the user has not verified
        self._assert_steps_displayed(
            response,
            [PayAndVerifyView.INTRO_STEP] + PayAndVerifyView.VERIFICATION_STEPS,
            PayAndVerifyView.INTRO_STEP
        )
        self._assert_messaging(response, PayAndVerifyView.FIRST_TIME_VERIFY_MSG)
        self._assert_requirements_displayed(response, [
            PayAndVerifyView.PHOTO_ID_REQ,
            PayAndVerifyView.WEBCAM_REQ,
        ])

    @ddt.data(
        ("verified", "submitted"),
        ("verified", "approved"),
        ("verified", "error"),
        ("professional", "submitted"),
        ("no-id-professional", None),
    )
    @ddt.unpack
    def test_start_flow_already_verified(self, course_mode, verification_status):
        course = self._create_course(course_mode)
        self._enroll(course.id, "honor")
        self._set_verification_status(verification_status)
        response = self._get_page('verify_student_start_flow', course.id)
        self._assert_displayed_mode(response, course_mode)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_messaging(response, PayAndVerifyView.FIRST_TIME_VERIFY_MSG)
        self._assert_requirements_displayed(response, [])

    @ddt.data("verified", "professional")
    def test_start_flow_already_paid(self, course_mode):
        course = self._create_course(course_mode)
        self._enroll(course.id, course_mode)
        response = self._get_page('verify_student_start_flow', course.id)
        self._assert_displayed_mode(response, course_mode)
        self._assert_steps_displayed(
            response,
            [PayAndVerifyView.INTRO_STEP] + PayAndVerifyView.VERIFICATION_STEPS,
            PayAndVerifyView.INTRO_STEP
        )
        self._assert_messaging(response, PayAndVerifyView.FIRST_TIME_VERIFY_MSG)
        self._assert_requirements_displayed(response, [
            PayAndVerifyView.PHOTO_ID_REQ,
            PayAndVerifyView.WEBCAM_REQ,
        ])

    def test_start_flow_not_enrolled(self):
        course = self._create_course("verified")
        self._set_verification_status("submitted")
        response = self._get_page('verify_student_start_flow', course.id)

        # This shouldn't happen if the student has been auto-enrolled,
        # but if they somehow end up on this page without enrolling,
        # treat them as if they need to pay
        response = self._get_page('verify_student_start_flow', course.id)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_requirements_displayed(response, [])

    def test_start_flow_unenrolled(self):
        course = self._create_course("verified")
        self._set_verification_status("submitted")
        self._enroll(course.id, "verified")
        self._unenroll(course.id)

        # If unenrolled, treat them like they haven't paid at all
        # (we assume that they've gotten a refund or didn't pay initially)
        response = self._get_page('verify_student_start_flow', course.id)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_requirements_displayed(response, [])

    @ddt.data(
        ("verified", "submitted"),
        ("verified", "approved"),
        ("professional", "submitted")
    )
    @ddt.unpack
    def test_start_flow_already_verified_and_paid(self, course_mode, verification_status):
        course = self._create_course(course_mode)
        self._enroll(course.id, course_mode)
        self._set_verification_status(verification_status)
        response = self._get_page(
            'verify_student_start_flow',
            course.id,
            expected_status_code=302
        )
        self._assert_redirects_to_dashboard(response)

    def test_verify_now(self):
        # We've already paid, and now we're trying to verify
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        response = self._get_page('verify_student_verify_now', course.id)

        self._assert_messaging(response, PayAndVerifyView.VERIFY_NOW_MSG)

        # Expect that *all* steps are displayed,
        # but we start after the payment step (because it's already completed).
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS + PayAndVerifyView.VERIFICATION_STEPS,
            PayAndVerifyView.FACE_PHOTO_STEP
        )

        # These will be hidden from the user anyway since they're starting
        # after the payment step.
        self._assert_requirements_displayed(response, [
            PayAndVerifyView.PHOTO_ID_REQ,
            PayAndVerifyView.WEBCAM_REQ,
        ])

    def test_verify_now_already_verified(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        self._set_verification_status("submitted")

        # Already verified, so if we somehow end up here,
        # redirect immediately to the dashboard
        response = self._get_page(
            'verify_student_verify_now',
            course.id,
            expected_status_code=302
        )
        self._assert_redirects_to_dashboard(response)

    def test_verify_now_user_details(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        response = self._get_page('verify_student_verify_now', course.id)
        self._assert_user_details(response, self.user.profile.name)

    @ddt.data(
        "verify_student_verify_now",
        "verify_student_verify_later",
        "verify_student_payment_confirmation"
    )
    def test_verify_now_or_later_not_enrolled(self, page_name):
        course = self._create_course("verified")
        response = self._get_page(page_name, course.id, expected_status_code=302)
        self._assert_redirects_to_start_flow(response, course.id)

    @ddt.data(
        "verify_student_verify_now",
        "verify_student_verify_later",
        "verify_student_payment_confirmation"
    )
    def test_verify_now_or_later_unenrolled(self, page_name):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        self._unenroll(course.id)
        response = self._get_page(page_name, course.id, expected_status_code=302)
        self._assert_redirects_to_start_flow(response, course.id)

    @ddt.data(
        "verify_student_verify_now",
        "verify_student_verify_later",
        "verify_student_payment_confirmation"
    )
    def test_verify_now_or_later_not_paid(self, page_name):
        course = self._create_course("verified")
        self._enroll(course.id, "honor")
        response = self._get_page(page_name, course.id, expected_status_code=302)
        self._assert_redirects_to_upgrade(response, course.id)

    def test_verify_later(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        response = self._get_page("verify_student_verify_later", course.id)

        self._assert_messaging(response, PayAndVerifyView.VERIFY_LATER_MSG)

        # Expect that the payment steps are NOT displayed
        self._assert_steps_displayed(
            response,
            [PayAndVerifyView.INTRO_STEP] + PayAndVerifyView.VERIFICATION_STEPS,
            PayAndVerifyView.INTRO_STEP
        )
        self._assert_requirements_displayed(response, [
            PayAndVerifyView.PHOTO_ID_REQ,
            PayAndVerifyView.WEBCAM_REQ,
        ])

    def test_verify_later_already_verified(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        self._set_verification_status("submitted")

        # Already verified, so if we somehow end up here,
        # redirect immediately to the dashboard
        response = self._get_page(
            'verify_student_verify_later',
            course.id,
            expected_status_code=302
        )
        self._assert_redirects_to_dashboard(response)

    def test_payment_confirmation(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        response = self._get_page('verify_student_payment_confirmation', course.id)

        self._assert_messaging(response, PayAndVerifyView.PAYMENT_CONFIRMATION_MSG)

        # Expect that *all* steps are displayed,
        # but we start at the payment confirmation step
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS + PayAndVerifyView.VERIFICATION_STEPS,
            PayAndVerifyView.PAYMENT_CONFIRMATION_STEP,
        )

        # These will be hidden from the user anyway since they're starting
        # after the payment step.  We're already including the payment
        # steps, so it's easier to include these as well.
        self._assert_requirements_displayed(response, [
            PayAndVerifyView.PHOTO_ID_REQ,
            PayAndVerifyView.WEBCAM_REQ,
        ])

    def test_payment_cannot_skip(self):
        """
         Simple test to verify that certain steps cannot be skipped. This test sets up
         a scenario where the user should be on the MAKE_PAYMENT_STEP, but is trying to
         skip it. Despite setting the parameter, the current step should still be
         MAKE_PAYMENT_STEP.
        """
        course = self._create_course("verified")
        response = self._get_page(
            'verify_student_start_flow',
            course.id,
            skip_first_step=True
        )

        self._assert_messaging(response, PayAndVerifyView.FIRST_TIME_VERIFY_MSG)

        # Expect that *all* steps are displayed,
        # but we start on the first verify step
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS + PayAndVerifyView.VERIFICATION_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP,
        )

    def test_payment_confirmation_already_verified(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        self._set_verification_status("submitted")

        response = self._get_page('verify_student_payment_confirmation', course.id)

        # Other pages would redirect to the dashboard at this point,
        # because the user has paid and verified.  However, we want
        # the user to see the confirmation page even if there
        # isn't anything for them to do here except return
        # to the dashboard.
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS,
            PayAndVerifyView.PAYMENT_CONFIRMATION_STEP,
        )

    def test_payment_confirmation_already_verified_skip_first_step(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        self._set_verification_status("submitted")

        response = self._get_page(
            'verify_student_payment_confirmation',
            course.id,
            skip_first_step=True
        )

        # There are no other steps, so stay on the
        # payment confirmation step
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS,
            PayAndVerifyView.PAYMENT_CONFIRMATION_STEP,
        )

    @ddt.data(
        (YESTERDAY, True),
        (TOMORROW, False)
    )
    @ddt.unpack
    def test_payment_confirmation_course_details(self, course_start, show_courseware_url):
        course = self._create_course("verified", course_start=course_start)
        self._enroll(course.id, "verified")
        response = self._get_page('verify_student_payment_confirmation', course.id)

        courseware_url = (
            reverse("course_root", kwargs={'course_id': unicode(course.id)})
            if show_courseware_url else ""
        )
        self._assert_course_details(
            response,
            unicode(course.id),
            course.display_name,
            course.start_datetime_text(),
            courseware_url
        )

    @ddt.data("verified", "professional")
    def test_upgrade(self, course_mode):
        course = self._create_course(course_mode)
        self._enroll(course.id, "honor")

        response = self._get_page('verify_student_upgrade_and_verify', course.id)
        self._assert_displayed_mode(response, course_mode)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS + PayAndVerifyView.VERIFICATION_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_messaging(response, PayAndVerifyView.UPGRADE_MSG)
        self._assert_requirements_displayed(response, [
            PayAndVerifyView.PHOTO_ID_REQ,
            PayAndVerifyView.WEBCAM_REQ,
        ])
        self._assert_upgrade_session_flag(True)

    def test_upgrade_already_verified(self):
        course = self._create_course("verified")
        self._enroll(course.id, "honor")
        self._set_verification_status("submitted")

        response = self._get_page('verify_student_upgrade_and_verify', course.id)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_messaging(response, PayAndVerifyView.UPGRADE_MSG)
        self._assert_requirements_displayed(response, [])

    def test_upgrade_already_paid(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")

        # If we've already paid, then the upgrade messaging
        # won't make much sense.  Redirect them to the
        # "verify later" page instead.
        response = self._get_page(
            'verify_student_upgrade_and_verify',
            course.id,
            expected_status_code=302
        )
        self._assert_redirects_to_verify_later(response, course.id)

    def test_upgrade_already_verified_and_paid(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        self._set_verification_status("submitted")

        # Already verified and paid, so redirect to the dashboard
        response = self._get_page(
            'verify_student_upgrade_and_verify',
            course.id,
            expected_status_code=302
        )
        self._assert_redirects_to_dashboard(response)

    def test_upgrade_not_enrolled(self):
        course = self._create_course("verified")
        response = self._get_page(
            'verify_student_upgrade_and_verify',
            course.id,
            expected_status_code=302
        )
        self._assert_redirects_to_start_flow(response, course.id)

    def test_upgrade_unenrolled(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        self._unenroll(course.id)
        response = self._get_page(
            'verify_student_upgrade_and_verify',
            course.id,
            expected_status_code=302
        )
        self._assert_redirects_to_start_flow(response, course.id)

    @ddt.data([], ["honor"], ["honor", "audit"])
    def test_no_verified_mode_for_course(self, modes_available):
        course = self._create_course(*modes_available)

        pages = [
            'verify_student_start_flow',
            'verify_student_verify_now',
            'verify_student_verify_later',
            'verify_student_upgrade_and_verify',
        ]

        for page_name in pages:
            self._get_page(
                page_name,
                course.id,
                expected_status_code=404
            )

    @ddt.data([], ["no-id-professional", "professional"], ["honor", "audit"])
    def test_no_id_professional_entry_point(self, modes_available):
        course = self._create_course(*modes_available)
        if "no-id-professional" in modes_available or "professional" in modes_available:
            self._get_page("verify_student_start_flow", course.id, expected_status_code=200)
        else:
            self._get_page("verify_student_start_flow", course.id, expected_status_code=404)

    @ddt.data(
        "verify_student_start_flow",
        "verify_student_verify_now",
        "verify_student_verify_later",
        "verify_student_upgrade_and_verify",
    )
    def test_require_login(self, url_name):
        self.client.logout()
        course = self._create_course("verified")
        response = self._get_page(url_name, course.id, expected_status_code=302)

        original_url = reverse(url_name, kwargs={'course_id': unicode(course.id)})
        login_url = u"{login_url}?next={original_url}".format(
            login_url=reverse('accounts_login'),
            original_url=original_url
        )
        self.assertRedirects(response, login_url)

    @ddt.data(
        "verify_student_start_flow",
        "verify_student_verify_now",
        "verify_student_verify_later",
        "verify_student_upgrade_and_verify",
    )
    def test_no_such_course(self, url_name):
        non_existent_course = CourseLocator(course="test", org="test", run="test")
        self._get_page(
            url_name,
            non_existent_course,
            expected_status_code=404
        )

    def test_account_not_active(self):
        self.user.is_active = False
        self.user.save()
        course = self._create_course("verified")
        response = self._get_page('verify_student_start_flow', course.id)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS + PayAndVerifyView.VERIFICATION_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_requirements_displayed(response, [
            PayAndVerifyView.ACCOUNT_ACTIVATION_REQ,
            PayAndVerifyView.PHOTO_ID_REQ,
            PayAndVerifyView.WEBCAM_REQ,
        ])

    def test_no_contribution(self):
        # Do NOT specify a contribution for the course in a session var.
        course = self._create_course("verified")
        response = self._get_page("verify_student_start_flow", course.id)
        self._assert_contribution_amount(response, "")

    def test_contribution_other_course(self):
        # Specify a contribution amount for another course in the session
        course = self._create_course("verified")
        other_course_id = CourseLocator(org="other", run="test", course="test")
        self._set_contribution("12.34", other_course_id)

        # Expect that the contribution amount is NOT pre-filled,
        response = self._get_page("verify_student_start_flow", course.id)
        self._assert_contribution_amount(response, "")

    def test_contribution(self):
        # Specify a contribution amount for this course in the session
        course = self._create_course("verified")
        self._set_contribution("12.34", course.id)

        # Expect that the contribution amount is pre-filled,
        response = self._get_page("verify_student_start_flow", course.id)
        self._assert_contribution_amount(response, "12.34")

    def test_verification_deadline(self):
        # Set a deadline on the course mode
        course = self._create_course("verified")
        mode = CourseMode.objects.get(
            course_id=course.id,
            mode_slug="verified"
        )
        expiration = datetime(2999, 1, 2, tzinfo=pytz.UTC)
        mode.expiration_datetime = expiration
        mode.save()

        # Expect that the expiration date is set
        response = self._get_page("verify_student_start_flow", course.id)
        data = self._get_page_data(response)
        self.assertEqual(data['verification_deadline'], "Jan 02, 2999 at 00:00 UTC")

    def test_course_mode_expired(self):
        course = self._create_course("verified")
        mode = CourseMode.objects.get(
            course_id=course.id,
            mode_slug="verified"
        )
        expiration = datetime(1999, 1, 2, tzinfo=pytz.UTC)
        mode.expiration_datetime = expiration
        mode.save()

        # Need to be enrolled
        self._enroll(course.id, "verified")

        # The course mode has expired, so expect an explanation
        # to the student that the deadline has passed
        response = self._get_page("verify_student_verify_later", course.id)
        self.assertContains(response, "verification deadline")
        self.assertContains(response, "Jan 02, 1999 at 00:00 UTC")

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_embargo_restrict(self):
        course = self._create_course("verified")
        with restrict_course(course.id) as redirect_url:
            # Simulate that we're embargoed from accessing this
            # course based on our IP address.
            response = self._get_page('verify_student_start_flow', course.id, expected_status_code=302)
            self.assertRedirects(response, redirect_url)

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_embargo_allow(self):
        course = self._create_course("verified")
        self._get_page('verify_student_start_flow', course.id)

    def _create_course(self, *course_modes, **kwargs):
        """Create a new course with the specified course modes. """
        course = CourseFactory.create()

        if kwargs.get('course_start'):
            course.start = kwargs.get('course_start')
            modulestore().update_item(course, ModuleStoreEnum.UserID.test)

        for course_mode in course_modes:
            min_price = (0 if course_mode in ["honor", "audit"] else self.MIN_PRICE)
            CourseModeFactory(
                course_id=course.id,
                mode_slug=course_mode,
                mode_display_name=course_mode,
                min_price=min_price
            )

        return course

    def _enroll(self, course_key, mode):
        """Enroll the user in a course. """
        CourseEnrollmentFactory.create(
            user=self.user,
            course_id=course_key,
            mode=mode
        )

    def _unenroll(self, course_key):
        """Unenroll the user from a course. """
        CourseEnrollment.unenroll(self.user, course_key)

    def _set_verification_status(self, status):
        """Set the user's photo verification status. """
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)

        if status in ["submitted", "approved", "expired", "denied", "error"]:
            attempt.mark_ready()
            attempt.submit()

        if status in ["approved", "expired"]:
            attempt.approve()
        elif status == "denied":
            attempt.deny("Denied!")
        elif status == "error":
            attempt.system_error("Error!")

        if status == "expired":
            days_good_for = settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
            attempt.created_at = datetime.now(pytz.UTC) - timedelta(days=(days_good_for + 1))
            attempt.save()

    def _set_contribution(self, amount, course_id):
        """Set the contribution amount pre-filled in a session var. """
        session = self.client.session
        session["donation_for_course"] = {
            unicode(course_id): amount
        }
        session.save()

    def _get_page(self, url_name, course_key, expected_status_code=200, skip_first_step=False):
        """Retrieve one of the verification pages. """
        url = reverse(url_name, kwargs={"course_id": unicode(course_key)})

        if skip_first_step:
            url += "?skip-first-step=1"

        response = self.client.get(url)
        self.assertEqual(response.status_code, expected_status_code)
        return response

    def _assert_displayed_mode(self, response, expected_mode):
        """Check whether a course mode is displayed. """
        response_dict = self._get_page_data(response)
        self.assertEqual(response_dict['course_mode_slug'], expected_mode)

    def _assert_steps_displayed(self, response, expected_steps, expected_current_step):
        """Check whether steps in the flow are displayed to the user. """
        response_dict = self._get_page_data(response)
        self.assertEqual(response_dict['current_step'], expected_current_step)
        self.assertEqual(expected_steps, [
            step['name'] for step in
            response_dict['display_steps']
        ])

    def _assert_messaging(self, response, expected_message):
        """Check the messaging on the page. """
        response_dict = self._get_page_data(response)
        self.assertEqual(response_dict['message_key'], expected_message)

    def _assert_requirements_displayed(self, response, requirements):
        """Check that requirements are displayed on the page. """
        response_dict = self._get_page_data(response)
        for req, displayed in response_dict['requirements'].iteritems():
            if req in requirements:
                self.assertTrue(displayed, msg="Expected '{req}' requirement to be displayed".format(req=req))
            else:
                self.assertFalse(displayed, msg="Expected '{req}' requirement to be hidden".format(req=req))

    def _assert_course_details(self, response, course_key, display_name, start_text, url):
        """Check the course information on the page. """
        response_dict = self._get_page_data(response)
        self.assertEqual(response_dict['course_key'], course_key)
        self.assertEqual(response_dict['course_name'], display_name)
        self.assertEqual(response_dict['course_start_date'], start_text)
        self.assertEqual(response_dict['courseware_url'], url)

    def _assert_user_details(self, response, full_name):
        """Check the user detail information on the page. """
        response_dict = self._get_page_data(response)
        self.assertEqual(response_dict['full_name'], full_name)

    def _assert_contribution_amount(self, response, expected_amount):
        """Check the pre-filled contribution amount. """
        response_dict = self._get_page_data(response)
        self.assertEqual(response_dict['contribution_amount'], expected_amount)

    def _get_page_data(self, response):
        """Retrieve the data attributes rendered on the page. """
        soup = BeautifulSoup(response.content)
        pay_and_verify_div = soup.find(id="pay-and-verify-container")
        return {
            'full_name': pay_and_verify_div['data-full-name'],
            'course_key': pay_and_verify_div['data-course-key'],
            'course_name': pay_and_verify_div['data-course-name'],
            'course_start_date': pay_and_verify_div['data-course-start-date'],
            'courseware_url': pay_and_verify_div['data-courseware-url'],
            'course_mode_name': pay_and_verify_div['data-course-mode-name'],
            'course_mode_slug': pay_and_verify_div['data-course-mode-slug'],
            'display_steps': json.loads(pay_and_verify_div['data-display-steps']),
            'current_step': pay_and_verify_div['data-current-step'],
            'requirements': json.loads(pay_and_verify_div['data-requirements']),
            'message_key': pay_and_verify_div['data-msg-key'],
            'contribution_amount': pay_and_verify_div['data-contribution-amount'],
            'verification_deadline': pay_and_verify_div['data-verification-deadline']
        }

    def _assert_upgrade_session_flag(self, is_upgrade):
        """Check that the session flag for attempting an upgrade is set. """
        self.assertEqual(self.client.session.get('attempting_upgrade'), is_upgrade)

    def _assert_redirects_to_dashboard(self, response):
        """Check that the page redirects to the student dashboard. """
        self.assertRedirects(response, reverse('dashboard'))

    def _assert_redirects_to_start_flow(self, response, course_id):
        """Check that the page redirects to the start of the payment/verification flow. """
        url = reverse('verify_student_start_flow', kwargs={'course_id': unicode(course_id)})
        self.assertRedirects(response, url)

    def _assert_redirects_to_verify_later(self, response, course_id):
        """Check that the page redirects to the "verify later" part of the flow. """
        url = reverse('verify_student_verify_later', kwargs={'course_id': unicode(course_id)})
        self.assertRedirects(response, url)

    def _assert_redirects_to_upgrade(self, response, course_id):
        """Check that the page redirects to the "upgrade" part of the flow. """
        url = reverse('verify_student_upgrade_and_verify', kwargs={'course_id': unicode(course_id)})
        self.assertRedirects(response, url)

    def test_course_upgrade_page_with_unicode_and_special_values_in_display_name(self):
        """Check the course information on the page. """
        mode_display_name = u"Introduction à l'astrophysique"
        course = CourseFactory.create(display_name=mode_display_name)
        for course_mode in ["honor", "verified"]:
            min_price = (self.MIN_PRICE if course_mode != "honor" else 0)
            CourseModeFactory(
                course_id=course.id,
                mode_slug=course_mode,
                mode_display_name=mode_display_name,
                min_price=min_price
            )

        self._enroll(course.id, "honor")
        response_dict = self._get_page_data(self._get_page('verify_student_start_flow', course.id))

        self.assertEqual(response_dict['course_name'], mode_display_name)


class TestCreateOrder(EcommerceApiTestMixin, ModuleStoreTestCase):
    """
    Tests for the create order view.
    """
    def setUp(self):
        """ Create a user and course. """
        super(TestCreateOrder, self).setUp()

        self.user = UserFactory.create(username="test", password="test")
        self.course = CourseFactory.create()
        for mode, min_price in (('audit', 0), ('honor', 0), ('verified', 100)):
            # Set SKU to empty string to ensure view knows how to handle such values
            CourseModeFactory(mode_slug=mode, course_id=self.course.id, min_price=min_price, sku='')
        self.client.login(username="test", password="test")

    def _post(self, data):
        """
        POST to the view being tested and return the response.
        """
        url = reverse('verify_student_create_order')
        return self.client.post(url, data)

    def test_create_order_already_verified(self):
        # Verify the student so we don't need to submit photos
        self._verify_student()

        # Create an order
        params = {
            'course_id': unicode(self.course.id),
            'contribution': 100
        }
        response = self._post(params)
        self.assertEqual(response.status_code, 200)

        # Verify that the information will be sent to the correct callback URL
        # (configured by test settings)
        data = json.loads(response.content)
        self.assertEqual(data['override_custom_receipt_page'], "http://testserver/shoppingcart/postpay_callback/")

        # Verify that the course ID and transaction type are included in "merchant-defined data"
        self.assertEqual(data['merchant_defined_data1'], unicode(self.course.id))
        self.assertEqual(data['merchant_defined_data2'], "verified")

    def test_create_order_already_verified_prof_ed(self):
        # Verify the student so we don't need to submit photos
        self._verify_student()

        # Create a prof ed course
        course = CourseFactory.create()
        CourseModeFactory(mode_slug="professional", course_id=course.id, min_price=10)

        # Create an order for a prof ed course
        params = {'course_id': unicode(course.id)}
        response = self._post(params)
        self.assertEqual(response.status_code, 200)

        # Verify that the course ID and transaction type are included in "merchant-defined data"
        data = json.loads(response.content)
        self.assertEqual(data['merchant_defined_data1'], unicode(course.id))
        self.assertEqual(data['merchant_defined_data2'], "professional")

    def test_create_order_for_no_id_professional(self):

        # Create a no-id-professional ed course
        course = CourseFactory.create()
        CourseModeFactory(mode_slug="no-id-professional", course_id=course.id, min_price=10)

        # Create an order for a prof ed course
        params = {'course_id': unicode(course.id)}
        response = self._post(params)
        self.assertEqual(response.status_code, 200)

        # Verify that the course ID and transaction type are included in "merchant-defined data"
        data = json.loads(response.content)
        self.assertEqual(data['merchant_defined_data1'], unicode(course.id))
        self.assertEqual(data['merchant_defined_data2'], "no-id-professional")

    def test_create_order_for_multiple_paid_modes(self):

        # Create a no-id-professional ed course
        course = CourseFactory.create()
        CourseModeFactory(mode_slug="no-id-professional", course_id=course.id, min_price=10)
        CourseModeFactory(mode_slug="professional", course_id=course.id, min_price=10)

        # Create an order for a prof ed course
        params = {'course_id': unicode(course.id)}
        response = self._post(params)
        self.assertEqual(response.status_code, 200)

        # Verify that the course ID and transaction type are included in "merchant-defined data"
        data = json.loads(response.content)
        self.assertEqual(data['merchant_defined_data1'], unicode(course.id))
        self.assertEqual(data['merchant_defined_data2'], "no-id-professional")

    def test_create_order_set_donation_amount(self):
        # Verify the student so we don't need to submit photos
        self._verify_student()

        # Create an order
        params = {
            'course_id': unicode(self.course.id),
            'contribution': '1.23'
        }
        self._post(params)

        # Verify that the client's session contains the new donation amount
        self.assertNotIn('donation_for_course', self.client.session)

    def _verify_student(self):
        """ Simulate that the student's identity has already been verified. """
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()
        attempt.approve()

    @override_settings(ECOMMERCE_API_URL=EcommerceApiTestMixin.ECOMMERCE_API_URL,
                       ECOMMERCE_API_SIGNING_KEY=EcommerceApiTestMixin.ECOMMERCE_API_SIGNING_KEY)
    def test_create_order_with_ecommerce_api(self):
        """ Verifies that the view communicates with the E-Commerce API to create orders. """
        # Keep track of the original number of orders to verify the old code is not being called.
        order_count = Order.objects.count()

        # Add SKU to CourseModes
        for course_mode in CourseMode.objects.filter(course_id=self.course.id):
            course_mode.sku = uuid4().hex.decode('ascii')
            course_mode.save()

        # Mock the E-Commerce Service response
        with self.mock_create_order():
            self._verify_student()
            params = {'course_id': unicode(self.course.id), 'contribution': 100}
            response = self._post(params)

        # Verify the response is correct.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.content), self.ECOMMERCE_API_SUCCESSFUL_BODY['payment_parameters'])

        # Verify old code is not called (e.g. no Order object created in LMS)
        self.assertEqual(order_count, Order.objects.count())

    def _add_course_mode_skus(self):
        """ Add SKUs to the CourseMode objects for self.course. """
        for course_mode in CourseMode.objects.filter(course_id=self.course.id):
            course_mode.sku = uuid4().hex.decode('ascii')
            course_mode.save()

    @override_settings(ECOMMERCE_API_URL=EcommerceApiTestMixin.ECOMMERCE_API_URL,
                       ECOMMERCE_API_SIGNING_KEY=EcommerceApiTestMixin.ECOMMERCE_API_SIGNING_KEY)
    def test_create_order_with_ecommerce_api_errors(self):
        """
        Verifies that the view communicates with the E-Commerce API to create orders, and handles errors
        appropriately.
        """
        self._add_course_mode_skus()

        with self.mock_create_order(side_effect=ApiError):
            self._verify_student()
            params = {'course_id': unicode(self.course.id), 'contribution': 100}
            self.assertRaises(ApiError, self._post, params)


class TestCreateOrderView(ModuleStoreTestCase):
    """
    Tests for the create_order view of verified course enrollment process.
    """
    # Minimum size valid image data
    IMAGE_DATA = ','

    def setUp(self):
        super(TestCreateOrderView, self).setUp()

        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course_id = 'Robot/999/Test_Course'
        self.course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        verified_mode = CourseMode(
            course_id=SlashSeparatedCourseKey("Robot", "999", 'Test_Course'),
            mode_slug="verified",
            mode_display_name="Verified Certificate",
            min_price=50
        )
        verified_mode.save()
        course_mode_post_data = {
            'certificate_mode': 'Select Certificate',
            'contribution': 50,
            'contribution-other-amt': '',
            'explain': ''
        }
        self.client.post(
            reverse("course_modes_choose", kwargs={'course_id': self.course_id}),
            course_mode_post_data
        )

    def test_invalid_photos_data(self):
        self._create_order(
            50,
            self.course_id,
            face_image='',
            photo_id_image='',
            expect_success=False
        )

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_invalid_amount(self):
        response = self._create_order(
            '1.a',
            self.course_id,
            face_image=self.IMAGE_DATA,
            photo_id_image=self.IMAGE_DATA,
            expect_status_code=400
        )
        self.assertIn('Selected price is not valid number.', response.content)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_invalid_mode(self):
        # Create a course that does not have a verified mode
        course_id = 'Fake/999/Test_Course'
        CourseFactory.create(org='Fake', number='999', display_name='Test Course')
        response = self._create_order(
            '50',
            course_id,
            face_image=self.IMAGE_DATA,
            photo_id_image=self.IMAGE_DATA,
            expect_status_code=400
        )
        self.assertIn('This course doesn\'t support paid certificates', response.content)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_create_order_fail_with_get(self):
        create_order_post_data = {
            'contribution': 50,
            'course_id': self.course_id,
            'face_image': self.IMAGE_DATA,
            'photo_id_image': self.IMAGE_DATA,
        }

        # Use the wrong HTTP method
        response = self.client.get(reverse('verify_student_create_order'), create_order_post_data)
        self.assertEqual(response.status_code, 405)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_create_order_success(self):
        response = self._create_order(
            50,
            self.course_id,
            face_image=self.IMAGE_DATA,
            photo_id_image=self.IMAGE_DATA
        )
        json_response = json.loads(response.content)
        self.assertIsNotNone(json_response.get('orderNumber'))

        # Verify that the order exists and is configured correctly
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, 'paying')
        item = CertificateItem.objects.get(order=order)
        self.assertEqual(item.status, 'paying')
        self.assertEqual(item.course_id, self.course.id)
        self.assertEqual(item.mode, 'verified')

    def _create_order(
            self, contribution, course_id,
            face_image=None,
            photo_id_image=None,
            expect_success=True,
            expect_status_code=200
    ):
        """Create a new order.

        Arguments:
            contribution (int): The contribution amount.
            course_id (CourseKey): The course to purchase.

        Keyword Arguments:
            face_image (string): Base-64 encoded image data
            photo_id_image (string): Base-64 encoded image data
            expect_success (bool): If True, verify that the response was successful.
            expect_status_code (int): The expected HTTP status code

        Returns:
            HttpResponse

        """
        url = reverse('verify_student_create_order')
        data = {
            'contribution': contribution,
            'course_id': course_id
        }

        if face_image is not None:
            data['face_image'] = face_image
        if photo_id_image is not None:
            data['photo_id_image'] = photo_id_image

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, expect_status_code)

        if expect_status_code == 200:
            json_response = json.loads(response.content)
            if expect_success:
                self.assertTrue(json_response.get('success'))
            else:
                self.assertFalse(json_response.get('success'))

        return response


@ddt.ddt
@patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
class TestSubmitPhotosForVerification(TestCase):
    """
    Tests for submitting photos for verification.
    """
    USERNAME = "test_user"
    PASSWORD = "test_password"
    IMAGE_DATA = "abcd,1234"
    FULL_NAME = u"Ḟüḷḷ Ṅäṁë"

    def setUp(self):
        super(TestSubmitPhotosForVerification, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result, msg="Could not log in")

    def test_submit_photos(self):
        # Submit the photos
        self._submit_photos(
            face_image=self.IMAGE_DATA,
            photo_id_image=self.IMAGE_DATA
        )

        # Verify that the attempt is created in the database
        attempt = SoftwareSecurePhotoVerification.objects.get(user=self.user)
        self.assertEqual(attempt.status, "submitted")

        # Verify that the user's name wasn't changed
        self._assert_user_name(self.user.profile.name)

    def test_submit_photos_and_change_name(self):
        # Submit the photos, along with a name change
        self._submit_photos(
            face_image=self.IMAGE_DATA,
            photo_id_image=self.IMAGE_DATA,
            full_name=self.FULL_NAME
        )

        # Check that the user's name was changed in the database
        self._assert_user_name(self.FULL_NAME)

    @ddt.data('face_image', 'photo_id_image')
    def test_invalid_image_data(self, invalid_param):
        params = {
            'face_image': self.IMAGE_DATA,
            'photo_id_image': self.IMAGE_DATA
        }
        params[invalid_param] = ""
        response = self._submit_photos(expected_status_code=400, **params)
        self.assertEqual(response.content, "Image data is not valid.")

    def test_invalid_name(self):
        response = self._submit_photos(
            face_image=self.IMAGE_DATA,
            photo_id_image=self.IMAGE_DATA,
            full_name="a",
            expected_status_code=400
        )
        self.assertEqual(response.content, "Name must be at least 2 characters long.")

    @ddt.data('face_image', 'photo_id_image')
    def test_missing_required_params(self, missing_param):
        params = {
            'face_image': self.IMAGE_DATA,
            'photo_id_image': self.IMAGE_DATA
        }
        del params[missing_param]
        response = self._submit_photos(expected_status_code=400, **params)
        self.assertEqual(
            response.content,
            "Missing required parameters: {missing}".format(missing=missing_param)
        )

    def _submit_photos(self, face_image=None, photo_id_image=None, full_name=None, expected_status_code=200):
        """Submit photos for verification.

        Keyword Arguments:
            face_image (str): The base-64 encoded face image data.
            photo_id_image (str): The base-64 encoded ID image data.
            full_name (unicode): The full name of the user, if the user is changing it.
            expected_status_code (int): The expected response status code.

        Returns:
            HttpResponse

        """
        url = reverse("verify_student_submit_photos")
        params = {}

        if face_image is not None:
            params['face_image'] = face_image

        if photo_id_image is not None:
            params['photo_id_image'] = photo_id_image

        if full_name is not None:
            params['full_name'] = full_name

        response = self.client.post(url, params)
        self.assertEqual(response.status_code, expected_status_code)

        if expected_status_code == 200:
            # Verify that photo submission confirmation email was sent
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual("Verification photos received", mail.outbox[0].subject)
        else:
            # Verify that photo submission confirmation email was not sent
            self.assertEqual(len(mail.outbox), 0)

        return response

    def _assert_user_name(self, full_name):
        """Check the user's name.

        Arguments:
            full_name (unicode): The user's full name.

        Raises:
            AssertionError

        """
        account_settings = get_account_settings(self.user)
        self.assertEqual(account_settings['name'], full_name)


class TestPhotoVerificationResultsCallback(ModuleStoreTestCase):
    """
    Tests for the results_callback view.
    """
    def setUp(self):
        super(TestPhotoVerificationResultsCallback, self).setUp()

        self.course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        self.course_id = self.course.id
        self.user = UserFactory.create()
        self.attempt = SoftwareSecurePhotoVerification(
            status="submitted",
            user=self.user
        )
        self.attempt.save()
        self.receipt_id = self.attempt.receipt_id
        self.client = Client()

    def mocked_has_valid_signature(method, headers_dict, body_dict, access_key, secret_key):  # pylint: disable=no-self-argument, unused-argument
        """
        Used as a side effect when mocking `verify_student.ssencrypt.has_valid_signature`.
        """
        return True

    def test_invalid_json(self):
        """
        Test for invalid json being posted by software secure.
        """
        data = {"Testing invalid"}
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB: testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('Invalid JSON', response.content)
        self.assertEqual(response.status_code, 400)

    def test_invalid_dict(self):
        """
        Test for invalid dictionary being posted by software secure.
        """
        data = '"\\"Test\\tTesting"'
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('JSON should be dict', response.content)
        self.assertEqual(response.status_code, 400)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_invalid_access_key(self):
        """
        Test for invalid access key.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": "Testing",
            "Reason": "Testing",
            "MessageType": "Testing"
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test testing:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('Access key invalid', response.content)
        self.assertEqual(response.status_code, 400)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_wrong_edx_id(self):
        """
        Test for wrong id of Software secure verification attempt.
        """
        data = {
            "EdX-ID": "Invalid-Id",
            "Result": "Testing",
            "Reason": "Testing",
            "MessageType": "Testing"
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('edX ID Invalid-Id not found', response.content)
        self.assertEqual(response.status_code, 400)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_pass_result(self):
        """
        Test for verification passed.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": "PASS",
            "Reason": "",
            "MessageType": "You have been verified."
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'), data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        attempt = SoftwareSecurePhotoVerification.objects.get(receipt_id=self.receipt_id)
        self.assertEqual(attempt.status, u'approved')
        self.assertEquals(response.content, 'OK!')

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_fail_result(self):
        """
        Test for failed verification.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": 'FAIL',
            "Reason": 'Invalid photo',
            "MessageType": 'Your photo doesn\'t meet standards.'
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        attempt = SoftwareSecurePhotoVerification.objects.get(receipt_id=self.receipt_id)
        self.assertEqual(attempt.status, u'denied')
        self.assertEqual(attempt.error_code, u'Your photo doesn\'t meet standards.')
        self.assertEqual(attempt.error_msg, u'"Invalid photo"')
        self.assertEquals(response.content, 'OK!')

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_system_fail_result(self):
        """
        Test for software secure result system failure.
        """
        data = {"EdX-ID": self.receipt_id,
                "Result": 'SYSTEM FAIL',
                "Reason": 'Memory overflow',
                "MessageType": 'You must retry the verification.'}
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        attempt = SoftwareSecurePhotoVerification.objects.get(receipt_id=self.receipt_id)
        self.assertEqual(attempt.status, u'must_retry')
        self.assertEqual(attempt.error_code, u'You must retry the verification.')
        self.assertEqual(attempt.error_msg, u'"Memory overflow"')
        self.assertEquals(response.content, 'OK!')

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_unknown_result(self):
        """
        test for unknown software secure result
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": 'Unknown',
            "Reason": 'Unknown reason',
            "MessageType": 'Unknown message'
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('Result Unknown not understood', response.content)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_reverification(self):
        """
         Test software secure result for reverification window.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": "PASS",
            "Reason": "",
            "MessageType": "You have been verified."
        }
        window = MidcourseReverificationWindowFactory(course_id=self.course_id)
        self.attempt.window = window
        self.attempt.save()
        json_data = json.dumps(data)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id).count(), 0)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertEquals(response.content, 'OK!')
        self.assertIsNotNone(CourseEnrollment.objects.get(course_id=self.course_id))


class TestReverifyView(ModuleStoreTestCase):
    """
    Tests for the reverification views
    """
    def setUp(self):
        super(TestReverifyView, self).setUp()

        self.user = UserFactory.create(username="rusty", password="test")
        self.user.profile.name = u"Røøsty Bøøgins"
        self.user.profile.save()
        self.client.login(username="rusty", password="test")
        self.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        self.course_key = self.course.id

    @patch('verify_student.views.render_to_response', render_mock)
    def test_reverify_get(self):
        url = reverse('verify_student_reverify')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        ((_template, context), _kwargs) = render_mock.call_args  # pylint: disable=unpacking-non-sequence
        self.assertFalse(context['error'])

    @patch('verify_student.views.render_to_response', render_mock)
    def test_reverify_post_failure(self):
        url = reverse('verify_student_reverify')
        response = self.client.post(url, {'face_image': '',
                                          'photo_id_image': ''})
        self.assertEquals(response.status_code, 200)
        ((template, context), _kwargs) = render_mock.call_args  # pylint: disable=unpacking-non-sequence
        self.assertIn('photo_reverification', template)
        self.assertTrue(context['error'])

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_reverify_post_success(self):
        url = reverse('verify_student_reverify')
        response = self.client.post(url, {'face_image': ',',
                                          'photo_id_image': ','})
        self.assertEquals(response.status_code, 302)
        try:
            verification_attempt = SoftwareSecurePhotoVerification.objects.get(user=self.user)
            self.assertIsNotNone(verification_attempt)
        except ObjectDoesNotExist:
            self.fail('No verification object generated')
        ((template, context), _kwargs) = render_mock.call_args  # pylint: disable=unpacking-non-sequence
        self.assertIn('photo_reverification', template)
        self.assertTrue(context['error'])


class TestMidCourseReverifyView(ModuleStoreTestCase):
    """
    Tests for the midcourse reverification views.
    """
    def setUp(self):
        super(TestMidCourseReverifyView, self).setUp()

        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course_key = SlashSeparatedCourseKey("Robot", "999", "Test_Course")
        CourseFactory.create(org='Robot', number='999', display_name='Test Course')

        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

    @patch('verify_student.views.render_to_response', render_mock)
    def test_midcourse_reverify_get(self):
        url = reverse('verify_student_midcourse_reverify',
                      kwargs={"course_id": self.course_key.to_deprecated_string()})
        response = self.client.get(url)

        self.mock_tracker.emit.assert_any_call(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.mode_changed',
            {
                'user_id': self.user.id,
                'course_id': self.course_key.to_deprecated_string(),
                'mode': "verified",
            }
        )

        # Check that user entering the reverify flow was logged, and that it was the last call
        self.mock_tracker.emit.assert_called_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.reverify.started',
            {
                'user_id': self.user.id,
                'course_id': self.course_key.to_deprecated_string(),
                'mode': "verified",
            }
        )

        self.assertTrue(self.mock_tracker.emit.call_count, 2)  # pylint: disable=no-member

        self.mock_tracker.emit.reset_mock()  # pylint: disable=no-member

        self.assertEquals(response.status_code, 200)
        ((_template, context), _kwargs) = render_mock.call_args  # pylint: disable=unpacking-non-sequence
        self.assertFalse(context['error'])

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_midcourse_reverify_post_success(self):
        window = MidcourseReverificationWindowFactory(course_id=self.course_key)
        url = reverse('verify_student_midcourse_reverify', kwargs={'course_id': self.course_key.to_deprecated_string()})

        response = self.client.post(url, {'face_image': ','})

        self.mock_tracker.emit.assert_any_call(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.mode_changed',
            {
                'user_id': self.user.id,
                'course_id': self.course_key.to_deprecated_string(),
                'mode': "verified",
            }
        )

        # Check that submission event was logged, and that it was the last call
        self.mock_tracker.emit.assert_called_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.reverify.submitted',
            {
                'user_id': self.user.id,
                'course_id': self.course_key.to_deprecated_string(),
                'mode': "verified",
            }
        )

        self.assertTrue(self.mock_tracker.emit.call_count, 2)  # pylint: disable=no-member

        self.mock_tracker.emit.reset_mock()  # pylint: disable=no-member

        self.assertEquals(response.status_code, 302)
        try:
            verification_attempt = SoftwareSecurePhotoVerification.objects.get(user=self.user, window=window)
            self.assertIsNotNone(verification_attempt)
        except ObjectDoesNotExist:
            self.fail('No verification object generated')

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_midcourse_reverify_post_failure_expired_window(self):
        window = MidcourseReverificationWindowFactory(
            course_id=self.course_key,
            start_date=datetime.now(pytz.UTC) - timedelta(days=100),
            end_date=datetime.now(pytz.UTC) - timedelta(days=50),
        )
        url = reverse('verify_student_midcourse_reverify', kwargs={'course_id': self.course_key.to_deprecated_string()})
        response = self.client.post(url, {'face_image': ','})
        self.assertEquals(response.status_code, 302)
        with self.assertRaises(ObjectDoesNotExist):
            SoftwareSecurePhotoVerification.objects.get(user=self.user, window=window)

    @patch('verify_student.views.render_to_response', render_mock)
    def test_midcourse_reverify_dash(self):
        url = reverse('verify_student_midcourse_reverify_dash')
        response = self.client.get(url)
        # not enrolled in any courses
        self.assertEquals(response.status_code, 200)

        enrollment = CourseEnrollment.get_or_create_enrollment(self.user, self.course_key)
        enrollment.update_enrollment(mode="verified", is_active=True)
        MidcourseReverificationWindowFactory(course_id=self.course_key)
        response = self.client.get(url)
        # enrolled in a verified course, and the window is open
        self.assertEquals(response.status_code, 200)

    @patch('verify_student.views.render_to_response', render_mock)
    def test_midcourse_reverify_invalid_course_id(self):
        # if course id is invalid return 400
        invalid_course_key = CourseLocator('edx', 'not', 'valid')
        url = reverse('verify_student_midcourse_reverify', kwargs={'course_id': unicode(invalid_course_key)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TestReverificationBanner(ModuleStoreTestCase):
    """
    Tests for toggling the "midcourse reverification failed" banner off.
    """

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def setUp(self):
        super(TestReverificationBanner, self).setUp()

        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course_id = 'Robot/999/Test_Course'
        CourseFactory.create(org='Robot', number='999', display_name=u'Test Course é')
        self.window = MidcourseReverificationWindowFactory(course_id=self.course_id)
        url = reverse('verify_student_midcourse_reverify', kwargs={'course_id': self.course_id})
        self.client.post(url, {'face_image': ','})
        photo_verification = SoftwareSecurePhotoVerification.objects.get(user=self.user, window=self.window)
        photo_verification.status = 'denied'
        photo_verification.save()

    def test_banner_display_off(self):
        self.client.post(reverse('verify_student_toggle_failed_banner_off'))
        photo_verification = SoftwareSecurePhotoVerification.objects.get(user=self.user, window=self.window)
        self.assertFalse(photo_verification.display)


class TestInCourseReverifyView(ModuleStoreTestCase):
    """
    Tests for the incourse reverification views.
    """
    IMAGE_DATA = "abcd,1234"
    MIDTERM = "midterm"

    def build_course(self):
        """
        Build up a course tree with a Reverificaiton xBlock.
        """
        # pylint: disable=attribute-defined-outside-init

        self.course_key = SlashSeparatedCourseKey("Robot", "999", "Test_Course")
        self.course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')

        # Create the course modes
        for mode in ('audit', 'honor', 'verified'):
            min_price = 0 if mode in ["honor", "audit"] else 1
            CourseModeFactory(mode_slug=mode, course_id=self.course_key, min_price=min_price)

        # Create the 'edx-reverification-block' in course tree
        section = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        subsection = ItemFactory.create(parent=section, category='sequential', display_name='Test Subsection')
        vertical = ItemFactory.create(parent=subsection, category='vertical', display_name='Test Unit')
        reverification = ItemFactory.create(
            parent=vertical,
            category='edx-reverification-block',
            display_name='Test Verification Block'
        )
        self.section_location = section.location
        self.subsection_location = subsection.location
        self.vertical_location = vertical.location
        self.reverification_location = reverification.location

    def setUp(self):
        super(TestInCourseReverifyView, self).setUp()

        self.build_course()

        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")

        # Enroll the user in the default mode (honor) to emulate
        CourseEnrollment.enroll(self.user, self.course_key, mode="verified")
        self.config = InCourseReverificationConfiguration(enabled=True)
        self.config.save()

        # mocking and patching for bi events
        analytics_patcher = patch('verify_student.views.analytics')
        self.mock_tracker = analytics_patcher.start()
        self.addCleanup(analytics_patcher.stop)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_feature_flag_get(self):
        self.config.enabled = False
        self.config.save()
        response = self.client.get(self._get_url(self.course_key, self.MIDTERM))
        self.assertEquals(response.status_code, 404)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_invalid_course_get(self):
        response = self.client.get(self._get_url("invalid/course/key", self.MIDTERM))

        self.assertEquals(response.status_code, 404)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_invalid_checkpoint_get(self):
        response = self.client.get(self._get_url(self.course_key, "invalid_checkpoint"))
        self.assertEquals(response.status_code, 404)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_initial_redirect_get(self):
        self._create_checkpoint()
        response = self.client.get(self._get_url(self.course_key, self.MIDTERM))

        url = reverse('verify_student_verify_later',
                      kwargs={"course_id": unicode(self.course_key)})
        self.assertRedirects(response, url)

    @override_settings(SEGMENT_IO_LMS_KEY="foobar")
    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True, 'SEGMENT_IO_LMS': True})
    def test_incourse_reverify_get(self):
        self._create_checkpoint()
        self._create_initial_verification()

        response = self.client.get(self._get_url(self.course_key, self.MIDTERM))
        self.assertEquals(response.status_code, 200)

        #Verify Google Analytics event fired after successfully submiting the picture
        self.mock_tracker.track.assert_called_once_with(  # pylint: disable=no-member
            self.user.id,  # pylint: disable=no-member
            EVENT_NAME_USER_ENTERED_INCOURSE_REVERIFY_VIEW,
            {
                'category': "verification",
                'label': unicode(self.course_key),
                'checkpoint': self.MIDTERM
            },

            context={
                'Google Analytics':
                {'clientId': None}
            }
        )
        self.mock_tracker.reset_mock()

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    @patch('verify_student.views.render_to_response', render_mock)
    def test_invalid_checkpoint_post(self):

        response = self.client.post(self._get_url(self.course_key, self.MIDTERM))
        self.assertEquals(response.status_code, 200)
        ((template, context), _kwargs) = render_mock.call_args  # pylint: disable=unpacking-non-sequence
        self.assertIn('incourse_reverify', template)
        self.assertTrue(context['error'])

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_initial_redirect_post(self):
        self._create_checkpoint()

        response = self.client.post(self._get_url(self.course_key, self.MIDTERM))
        url = reverse('verify_student_verify_later',
                      kwargs={"course_id": unicode(self.course_key)})

        self.assertRedirects(response, url)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_index_error_post(self):
        self._create_checkpoint()
        self._create_initial_verification()

        response = self.client.post(self._get_url(self.course_key, self.MIDTERM), {"face_image": ""})
        self.assertEqual(response.status_code, 400)

    @override_settings(SEGMENT_IO_LMS_KEY="foobar")
    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True, 'SEGMENT_IO_LMS': True})
    def test_incourse_reverify_post(self):
        self._create_checkpoint()
        self._create_initial_verification()

        response = self.client.post(self._get_url(self.course_key, self.MIDTERM), {"face_image": self.IMAGE_DATA})
        self.assertEqual(response.status_code, 200)

        #Verify Google Analytics event fired after successfully submiting the picture
        self.mock_tracker.track.assert_called_once_with(  # pylint: disable=no-member
            self.user.id,  # pylint: disable=no-member
            EVENT_NAME_USER_SUBMITTED_INCOURSE_REVERIFY,
            {
                'category': "verification",
                'label': unicode(self.course_key),
                'checkpoint': self.MIDTERM
            },

            context={
                'Google Analytics':
                {'clientId': None}
            }
        )
        self.mock_tracker.reset_mock()

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_feature_flag_post(self):
        self.config.enabled = False
        self.config.save()

        response = self.client.post(self._get_url(self.course_key, self.MIDTERM))
        self.assertEquals(response.status_code, 404)

    def _create_checkpoint(self):
        """helper method for creating checkpoint"""
        checkpoint = VerificationCheckpoint(course_id=self.course_key, checkpoint_name=self.MIDTERM)
        checkpoint.save()

    def _create_initial_verification(self):
        """helper method for initial verification"""
        attempt = SoftwareSecurePhotoVerification(user=self.user)
        attempt.mark_ready()
        attempt.save()
        attempt.submit()

    def _get_url(self, course_key, checkpoint):
        """contruct the url.

       Arguments:
            course_key (unicode): The ID of the course.
            checkpoint (str): The verification checkpoint
        Returns:
            url

        """
        return reverse('verify_student_incourse_reverify',
                       kwargs={
                           "course_id": unicode(course_key),
                           "checkpoint_name": checkpoint,
                           "location": unicode(self.reverification_location)
                       })

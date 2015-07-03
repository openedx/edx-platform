# encoding: utf-8
"""
Tests of verify_student views.
"""

import json
import urllib
from datetime import timedelta, datetime
from uuid import uuid4

import ddt
import httpretty
import mock
import pytz
from bs4 import BeautifulSoup
from mock import patch, Mock, ANY

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core import mail
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from django.utils import timezone

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.locator import CourseLocator
from opaque_keys.edx.keys import UsageKey

from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from courseware.url_helpers import get_redirect_url
from commerce.tests import TEST_PAYMENT_DATA, TEST_API_URL, TEST_API_SIGNING_KEY
from embargo.test_utils import restrict_course
from microsite_configuration import microsite
from openedx.core.djangoapps.user_api.accounts.api import get_account_settings
from shoppingcart.models import Order, CertificateItem
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from student.models import CourseEnrollment
from util.date_utils import get_default_time_display
from util.testing import UrlResetMixin
from verify_student.views import (
    checkout_with_ecommerce_service, render_to_response, PayAndVerifyView,
    _send_email, _compose_message_reverification_email
)
from verify_student.models import (
    SoftwareSecurePhotoVerification, VerificationCheckpoint,
    InCourseReverificationConfiguration, VerificationStatus
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import check_mongo_calls


def mock_render_to_response(*args, **kwargs):
    return render_to_response(*args, **kwargs)

render_mock = Mock(side_effect=mock_render_to_response)

PAYMENT_DATA_KEYS = {'payment_processor_name', 'payment_page_url', 'payment_form_data'}


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
        "verify_student_payment_confirmation"
    )
    def test_verify_now_not_enrolled(self, page_name):
        course = self._create_course("verified")
        response = self._get_page(page_name, course.id, expected_status_code=302)
        self._assert_redirects_to_start_flow(response, course.id)

    @ddt.data(
        "verify_student_verify_now",
        "verify_student_payment_confirmation"
    )
    def test_verify_now_unenrolled(self, page_name):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        self._unenroll(course.id)
        response = self._get_page(page_name, course.id, expected_status_code=302)
        self._assert_redirects_to_start_flow(response, course.id)

    @ddt.data(
        "verify_student_verify_now",
        "verify_student_payment_confirmation"
    )
    def test_verify_now_not_paid(self, page_name):
        course = self._create_course("verified")
        self._enroll(course.id, "honor")
        response = self._get_page(page_name, course.id, expected_status_code=302)
        self._assert_redirects_to_upgrade(response, course.id)

    def test_verify_later(self):
        """ The deprecated verify-later page should redirect to the verification start page. """
        course = self._create_course("verified")
        course_key = course.id
        self._enroll(course_key, "verified")
        response = self._get_page("verify_student_verify_later", course_key, expected_status_code=301)
        self._assert_redirects_to_verify_start(response, course_key, 301)

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
        self._assert_redirects_to_verify_start(response, course.id)

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
        "verify_student_upgrade_and_verify",
    )
    def test_require_login(self, url_name):
        self.client.logout()
        course = self._create_course("verified")
        response = self._get_page(url_name, course.id, expected_status_code=302)

        original_url = reverse(url_name, kwargs={'course_id': unicode(course.id)})
        login_url = u"{login_url}?next={original_url}".format(
            login_url=reverse('signin_user'),
            original_url=original_url
        )
        self.assertRedirects(response, login_url)

    @ddt.data(
        "verify_student_start_flow",
        "verify_student_verify_now",
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
        response = self._get_page("verify_student_verify_now", course.id)
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

        mode_kwargs = {}
        if kwargs.get('sku'):
            mode_kwargs['sku'] = kwargs['sku']

        for course_mode in course_modes:
            min_price = (0 if course_mode in ["honor", "audit"] else self.MIN_PRICE)
            CourseModeFactory(
                course_id=course.id,
                mode_slug=course_mode,
                mode_display_name=course_mode,
                min_price=min_price,
                **mode_kwargs
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

    def _assert_redirects_to_verify_start(self, response, course_id, status_code=302):
        """Check that the page redirects to the "verify later" part of the flow. """
        url = reverse('verify_student_verify_now', kwargs={'course_id': unicode(course_id)})
        self.assertRedirects(response, url, status_code)

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

    @httpretty.activate
    @override_settings(ECOMMERCE_API_URL=TEST_API_URL, ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY)
    def test_processors_api(self):
        """
        Check that when working with a product being processed by the
        ecommerce api, we correctly call to that api for the list of
        available payment processors.
        """
        # setting a nonempty sku on the course will a trigger calls to
        # the ecommerce api to get payment processors.
        course = self._create_course("verified", sku='nonempty-sku')
        self._enroll(course.id, "honor")

        # mock out the payment processors endpoint
        httpretty.register_uri(
            httpretty.GET,
            "{}/payment/processors/".format(TEST_API_URL),
            body=json.dumps(['foo', 'bar']),
            content_type="application/json",
        )
        # make the server request
        response = self._get_page('verify_student_start_flow', course.id)
        self.assertEqual(response.status_code, 200)

        # ensure the mock api call was made.  NOTE: the following line
        # approximates the check - if the headers were empty it means
        # there was no last request.
        self.assertNotEqual(httpretty.last_request().headers, {})


class CheckoutTestMixin(object):
    """
    Mixin implementing test methods that should behave identically regardless
    of which backend is used (shoppingcart or ecommerce service).  Subclasses
    immediately follow for each backend, which inherit from TestCase and
    define methods needed to customize test parameters, and patch the
    appropriate checkout method.

    Though the view endpoint under test is named 'create_order' for backward-
    compatibility, the effect of using this endpoint is to choose a specific product
    (i.e. course mode) and trigger immediate checkout.
    """
    def setUp(self):
        """ Create a user and course. """
        super(CheckoutTestMixin, self).setUp()

        self.user = UserFactory.create(username="test", password="test")
        self.course = CourseFactory.create()
        for mode, min_price in (('audit', 0), ('honor', 0), ('verified', 100)):
            CourseModeFactory(mode_slug=mode, course_id=self.course.id, min_price=min_price, sku=self.make_sku())
        self.client.login(username="test", password="test")

    def _assert_checked_out(
            self,
            post_params,
            patched_create_order,
            expected_course_key,
            expected_mode_slug,
            expected_status_code=200
    ):
        """
        DRY helper.

        Ensures that checkout functions were invoked as
        expected during execution of the create_order endpoint.
        """
        post_params.setdefault('processor', None)
        response = self.client.post(reverse('verify_student_create_order'), post_params)
        self.assertEqual(response.status_code, expected_status_code)
        if expected_status_code == 200:
            # ensure we called checkout at all
            self.assertTrue(patched_create_order.called)
            # ensure checkout args were correct
            args = self._get_checkout_args(patched_create_order)
            self.assertEqual(args['user'], self.user)
            self.assertEqual(args['course_key'], expected_course_key)
            self.assertEqual(args['course_mode'].slug, expected_mode_slug)
            # ensure response data was correct
            data = json.loads(response.content)
            self.assertEqual(set(data.keys()), PAYMENT_DATA_KEYS)
        else:
            self.assertFalse(patched_create_order.called)

    def test_create_order(self, patched_create_order):
        # Create an order
        params = {
            'course_id': unicode(self.course.id),
            'contribution': 100,
        }
        self._assert_checked_out(params, patched_create_order, self.course.id, 'verified')

    def test_create_order_prof_ed(self, patched_create_order):
        # Create a prof ed course
        course = CourseFactory.create()
        CourseModeFactory(mode_slug="professional", course_id=course.id, min_price=10, sku=self.make_sku())
        # Create an order for a prof ed course
        params = {'course_id': unicode(course.id)}
        self._assert_checked_out(params, patched_create_order, course.id, 'professional')

    def test_create_order_no_id_professional(self, patched_create_order):
        # Create a no-id-professional ed course
        course = CourseFactory.create()
        CourseModeFactory(mode_slug="no-id-professional", course_id=course.id, min_price=10, sku=self.make_sku())
        # Create an order for a prof ed course
        params = {'course_id': unicode(course.id)}
        self._assert_checked_out(params, patched_create_order, course.id, 'no-id-professional')

    def test_create_order_for_multiple_paid_modes(self, patched_create_order):
        # Create a no-id-professional ed course
        course = CourseFactory.create()
        CourseModeFactory(mode_slug="no-id-professional", course_id=course.id, min_price=10, sku=self.make_sku())
        CourseModeFactory(mode_slug="professional", course_id=course.id, min_price=10, sku=self.make_sku())
        # Create an order for a prof ed course
        params = {'course_id': unicode(course.id)}
        # TODO jsa - is this the intended behavior?
        self._assert_checked_out(params, patched_create_order, course.id, 'no-id-professional')

    def test_create_order_bad_donation_amount(self, patched_create_order):
        # Create an order
        params = {
            'course_id': unicode(self.course.id),
            'contribution': '99.9'
        }
        self._assert_checked_out(params, patched_create_order, None, None, expected_status_code=400)

    def test_create_order_good_donation_amount(self, patched_create_order):
        # Create an order
        params = {
            'course_id': unicode(self.course.id),
            'contribution': '100.0'
        }
        self._assert_checked_out(params, patched_create_order, self.course.id, 'verified')

    def test_old_clients(self, patched_create_order):
        # ensure the response to a request from a stale js client is modified so as
        # not to break behavior in the browser.
        # (XCOM-214) remove after release.
        expected_payment_data = TEST_PAYMENT_DATA.copy()
        expected_payment_data['payment_form_data'].update({'foo': 'bar'})
        patched_create_order.return_value = expected_payment_data
        # there is no 'processor' parameter in the post payload, so the response should only contain payment form data.
        params = {'course_id': unicode(self.course.id), 'contribution': 100}
        response = self.client.post(reverse('verify_student_create_order'), params)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(patched_create_order.called)
        # ensure checkout args were correct
        args = self._get_checkout_args(patched_create_order)
        self.assertEqual(args['user'], self.user)
        self.assertEqual(args['course_key'], self.course.id)
        self.assertEqual(args['course_mode'].slug, 'verified')
        # ensure response data was correct
        data = json.loads(response.content)
        self.assertEqual(data, {'foo': 'bar'})


@patch('verify_student.views.checkout_with_shoppingcart', return_value=TEST_PAYMENT_DATA)
class TestCreateOrderShoppingCart(CheckoutTestMixin, ModuleStoreTestCase):
    """ Test view behavior when the shoppingcart is used. """

    def make_sku(self):
        """ Checkout is handled by shoppingcart when the course mode's sku is empty. """
        return ''

    def _get_checkout_args(self, patched_create_order):
        """ Assuming patched_create_order was called, return a mapping containing the call arguments."""
        return dict(zip(('request', 'user', 'course_key', 'course_mode', 'amount'), patched_create_order.call_args[0]))


@override_settings(ECOMMERCE_API_URL=TEST_API_URL, ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY)
@patch('verify_student.views.checkout_with_ecommerce_service', return_value=TEST_PAYMENT_DATA)
class TestCreateOrderEcommerceService(CheckoutTestMixin, ModuleStoreTestCase):
    """ Test view behavior when the ecommerce service is used. """

    def make_sku(self):
        """ Checkout is handled by the ecommerce service when the course mode's sku is nonempty. """
        return uuid4().hex.decode('ascii')

    def _get_checkout_args(self, patched_create_order):
        """ Assuming patched_create_order was called, return a mapping containing the call arguments."""
        return dict(zip(('user', 'course_key', 'course_mode', 'processor'), patched_create_order.call_args[0]))


class TestCheckoutWithEcommerceService(ModuleStoreTestCase):
    """
    Ensures correct behavior in the function `checkout_with_ecommerce_service`.
    """

    @httpretty.activate
    @override_settings(ECOMMERCE_API_URL=TEST_API_URL, ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY)
    def test_create_basket(self):
        """
        Check that when working with a product being processed by the
        ecommerce api, we correctly call to that api to create a basket.
        """
        user = UserFactory.create(username="test-username")
        course_mode = CourseModeFactory(sku="test-sku").to_tuple()  # pylint: disable=no-member
        expected_payment_data = {'foo': 'bar'}
        # mock out the payment processors endpoint
        httpretty.register_uri(
            httpretty.POST,
            "{}/baskets/".format(TEST_API_URL),
            body=json.dumps({'payment_data': expected_payment_data}),
            content_type="application/json",
        )

        with mock.patch('verify_student.views.audit_log') as mock_audit_log:
            # Call the function
            actual_payment_data = checkout_with_ecommerce_service(
                user,
                'dummy-course-key',
                course_mode,
                'test-processor'
            )

            # Verify that an audit message was logged
            self.assertTrue(mock_audit_log.called)

        # Check the api call
        self.assertEqual(json.loads(httpretty.last_request().body), {
            'products': [{'sku': 'test-sku'}],
            'checkout': True,
            'payment_processor_name': 'test-processor',
        })
        # Check the response
        self.assertEqual(actual_payment_data, expected_payment_data)


class TestCreateOrderView(ModuleStoreTestCase):
    """
    Tests for the create_order view of verified course enrollment process.
    """

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

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_invalid_amount(self):
        response = self._create_order('1.a', self.course_id, expect_status_code=400)
        self.assertIn('Selected price is not valid number.', response.content)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_invalid_mode(self):
        # Create a course that does not have a verified mode
        course_id = 'Fake/999/Test_Course'
        CourseFactory.create(org='Fake', number='999', display_name='Test Course')
        response = self._create_order('50', course_id, expect_status_code=400)
        self.assertIn('This course doesn\'t support paid certificates', response.content)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_create_order_fail_with_get(self):
        create_order_post_data = {
            'contribution': 50,
            'course_id': self.course_id,
        }

        # Use the wrong HTTP method
        response = self.client.get(reverse('verify_student_create_order'), create_order_post_data)
        self.assertEqual(response.status_code, 405)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_create_order_success(self):
        response = self._create_order(50, self.course_id)
        json_response = json.loads(response.content)
        self.assertIsNotNone(json_response['payment_form_data'].get('orderNumber'))  # TODO not canonical

        # Verify that the order exists and is configured correctly
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, 'paying')
        item = CertificateItem.objects.get(order=order)
        self.assertEqual(item.status, 'paying')
        self.assertEqual(item.course_id, self.course.id)
        self.assertEqual(item.mode, 'verified')

    def _create_order(self, contribution, course_id, expect_success=True, expect_status_code=200):
        """Create a new order.

        Arguments:
            contribution (int): The contribution amount.
            course_id (CourseKey): The course to purchase.

        Keyword Arguments:
            expect_success (bool): If True, verify that the response was successful.
            expect_status_code (int): The expected HTTP status code

        Returns:
            HttpResponse

        """
        url = reverse('verify_student_create_order')
        data = {
            'contribution': contribution,
            'course_id': course_id,
            'processor': None,
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, expect_status_code)

        if expect_status_code == 200:
            json_response = json.loads(response.content)
            if expect_success:
                self.assertEqual(set(json_response.keys()), PAYMENT_DATA_KEYS)
            else:
                self.assertFalse(json_response['success'])

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
    def test_in_course_reverify_disabled(self):
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
        # Verify that photo submission confirmation email was sent
        self.assertEqual(len(mail.outbox), 0)
        user_status = VerificationStatus.objects.filter(user=self.user).count()
        self.assertEqual(user_status, 0)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_pass_in_course_reverify_result(self):
        """
        Test for verification passed.
        """
        self.create_reverification_xblock()

        incourse_reverify_enabled = InCourseReverificationConfiguration.current()
        incourse_reverify_enabled.enabled = True
        incourse_reverify_enabled.save()

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
        # Verify that photo re-verification status email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual("Re-verification Status", mail.outbox[0].subject)

    @mock.patch('verify_student.views._send_email')
    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_reverification_on_callback(self, mock_send_email):
        """
        Test software secure callback flow for re-verification.
        """
        # Create the 'edx-reverification-block' in course tree
        self.create_reverification_xblock()

        # create dummy data for software secure photo verification result callback
        data = {
            "EdX-ID": self.receipt_id,
            "Result": "PASS",
            "Reason": "",
            "MessageType": "You have been verified."
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertEqual(response.content, 'OK!')

        # now check that '_send_email' method is called on result callback
        # with required parameters
        subject = "Re-verification Status"
        mock_send_email.assert_called_once_with(self.user.id, subject, ANY)

    def create_reverification_xblock(self):
        """
        Create the reverification XBlock.
        """
        # Create the 'edx-reverification-block' in course tree
        section = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        subsection = ItemFactory.create(parent=section, category='sequential', display_name='Test Subsection')
        vertical = ItemFactory.create(parent=subsection, category='vertical', display_name='Test Unit')
        reverification = ItemFactory.create(
            parent=vertical,
            category='edx-reverification-block',
            display_name='Test Verification Block'
        )

        # Create checkpoint
        checkpoint = VerificationCheckpoint(course_id=self.course_id, checkpoint_location=reverification.location)
        checkpoint.save()

        # Add a re-verification attempt
        checkpoint.add_verification_attempt(self.attempt)

        # Add a re-verification attempt status for the user
        VerificationStatus.add_verification_status(checkpoint, self.user, "submitted")


class TestReverifyView(TestCase):
    """
    Tests for the reverification view.

    Reverification occurs when a verification attempt is denied or expired,
    and the student is given the option to resubmit.
    """

    USERNAME = "shaftoe"
    PASSWORD = "detachment-2702"

    def setUp(self):
        super(TestReverifyView, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        success = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(success, msg="Could not log in")

    def test_reverify_view_can_reverify_denied(self):
        # User has a denied attempt, so can reverify
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()
        attempt.deny("error")
        self._assert_can_reverify()

    def test_reverify_view_can_reverify_expired(self):
        # User has a verification attempt, but it's expired
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()
        attempt.approve()

        days_good_for = settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
        attempt.created_at = datetime.now(pytz.UTC) - timedelta(days=(days_good_for + 1))
        attempt.save()

        # Allow the student to reverify
        self._assert_can_reverify()

    def test_reverify_view_cannot_reverify_pending(self):
        # User has submitted a verification attempt, but Software Secure has not yet responded
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()

        # Cannot reverify because an attempt has already been submitted.
        self._assert_cannot_reverify()

    def test_reverify_view_cannot_reverify_approved(self):
        # Submitted attempt has been approved
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()
        attempt.approve()

        # Cannot reverify because the user is already verified.
        self._assert_cannot_reverify()

    def _get_reverify_page(self):
        """
        Retrieve the reverification page and return the response.
        """
        url = reverse("verify_student_reverify")
        return self.client.get(url)

    def _assert_can_reverify(self):
        """
        Check that the reverification flow is rendered.
        """
        response = self._get_reverify_page()
        self.assertContains(response, "reverify-container")

    def _assert_cannot_reverify(self):
        """
        Check that the user is blocked from reverifying.
        """
        response = self._get_reverify_page()
        self.assertContains(response, "reverify-blocked")


class TestInCourseReverifyView(ModuleStoreTestCase):
    """
    Tests for the incourse reverification views.
    """
    IMAGE_DATA = "abcd,1234"

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
        self.reverification = ItemFactory.create(
            parent=vertical,
            category='edx-reverification-block',
            display_name='Test Verification Block'
        )
        self.section_location = section.location
        self.subsection_location = subsection.location
        self.vertical_location = vertical.location
        self.reverification_location = unicode(self.reverification.location)
        self.reverification_assessment = self.reverification.related_assessment

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
        response = self.client.get(self._get_url(self.course_key, self.reverification_location))
        self.assertEquals(response.status_code, 404)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_invalid_course_get(self):
        response = self.client.get(self._get_url("invalid/course/key", self.reverification_location))

        self.assertEquals(response.status_code, 404)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_invalid_checkpoint_get(self):
        response = self.client.get(self._get_url(self.course_key, "invalid_checkpoint"))
        self.assertEquals(response.status_code, 404)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_initial_redirect_get(self):
        self._create_checkpoint()
        response = self.client.get(self._get_url(self.course_key, self.reverification_location))

        url = reverse('verify_student_verify_now', kwargs={"course_id": unicode(self.course_key)})
        self.assertRedirects(response, url)

    @override_settings(SEGMENT_IO_LMS_KEY="foobar")
    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True, 'SEGMENT_IO_LMS': True})
    def test_incourse_reverify_get(self):
        """
        Test incourse reverification.
        """
        self._create_checkpoint()
        self._create_initial_verification()

        response = self.client.get(self._get_url(self.course_key, self.reverification_location))
        self.assertEquals(response.status_code, 200)

        # verify that Google Analytics event fires after successfully
        # submitting the photo verification
        self.mock_tracker.track.assert_called_once_with(  # pylint: disable=no-member
            self.user.id,  # pylint: disable=no-member
            'edx.bi.reverify.started',
            {
                'category': "verification",
                'label': unicode(self.course_key),
                'checkpoint': self.reverification_assessment
            },

            context={
                'Google Analytics':
                {'clientId': None}
            }
        )
        self.mock_tracker.reset_mock()

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_checkpoint_post(self):
        """Verify that POST requests including an invalid checkpoint location
        results in a 400 response.
        """
        response = self.client.post(self._get_url(self.course_key, self.reverification_location))
        self.assertEquals(response.status_code, 400)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_initial_redirect_post(self):
        self._create_checkpoint()
        response = self.client.post(self._get_url(self.course_key, self.reverification_location))

        url = reverse('verify_student_verify_now', kwargs={"course_id": unicode(self.course_key)})
        self.assertRedirects(response, url)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_incourse_reverify_index_error_post(self):
        self._create_checkpoint()
        self._create_initial_verification()

        response = self.client.post(self._get_url(self.course_key, self.reverification_location), {"face_image": ""})
        self.assertEqual(response.status_code, 400)

    @override_settings(SEGMENT_IO_LMS_KEY="foobar")
    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True, 'SEGMENT_IO_LMS': True})
    def test_incourse_reverify_post(self):
        self._create_checkpoint()
        self._create_initial_verification()

        response = self.client.post(
            self._get_url(self.course_key, self.reverification_location),
            {"face_image": self.IMAGE_DATA}
        )
        self.assertEqual(response.status_code, 200)

        # test that Google Analytics event firs after successfully submitting
        # photo verification
        self.mock_tracker.track.assert_called_once_with(  # pylint: disable=no-member
            self.user.id,
            'edx.bi.reverify.submitted',
            {
                'category': "verification",
                'label': unicode(self.course_key),
                'checkpoint': self.reverification_assessment
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

        response = self.client.post(self._get_url(self.course_key, self.reverification_location))
        self.assertEquals(response.status_code, 404)

    def _create_checkpoint(self):
        """
        Helper method for creating a reverification checkpoint.
        """
        checkpoint = VerificationCheckpoint(course_id=self.course_key, checkpoint_location=self.reverification_location)
        checkpoint.save()

    def _create_initial_verification(self):
        """
        Helper method for initial verification.
        """
        attempt = SoftwareSecurePhotoVerification(user=self.user)
        attempt.mark_ready()
        attempt.save()
        attempt.submit()

    def _get_url(self, course_key, checkpoint_location):
        """
        Construct the reverification url.

        Arguments:
            course_key (unicode): The ID of the course
            checkpoint_location (str): Location of verification checkpoint

        Returns:
            url
        """
        return reverse(
            'verify_student_incourse_reverify',
            kwargs={
                "course_id": unicode(course_key),
                "usage_id": checkpoint_location
            }
        )


class TestEmailMessageWithCustomICRVBlock(ModuleStoreTestCase):
    """
    Test email sending on re-verification
    """

    def build_course(self):
        """
        Build up a course tree with a Reverificaiton xBlock.
        """
        self.course_key = SlashSeparatedCourseKey("Robot", "999", "Test_Course")
        self.course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        self.due_date = datetime.now(pytz.UTC) + timedelta(days=20)
        self.allowed_attempts = 1

        # Create the course modes
        for mode in ('audit', 'honor', 'verified'):
            min_price = 0 if mode in ["honor", "audit"] else 1
            CourseModeFactory(mode_slug=mode, course_id=self.course_key, min_price=min_price)

        # Create the 'edx-reverification-block' in course tree
        section = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        subsection = ItemFactory.create(parent=section, category='sequential', display_name='Test Subsection')
        vertical = ItemFactory.create(parent=subsection, category='vertical', display_name='Test Unit')

        self.reverification = ItemFactory.create(
            parent=vertical,
            category='edx-reverification-block',
            display_name='Test Verification Block',
            metadata={'attempts': self.allowed_attempts, 'due': self.due_date}
        )

        self.section_location = section.location
        self.subsection_location = subsection.location
        self.vertical_location = vertical.location
        self.reverification_location = unicode(self.reverification.location)
        self.assessment = self.reverification.related_assessment

        self.re_verification_link = reverse(
            'verify_student_incourse_reverify',
            args=(
                unicode(self.course_key),
                self.reverification_location
            )
        )

    def setUp(self):
        """
        Setup method for testing photo verification email messages.
        """
        super(TestEmailMessageWithCustomICRVBlock, self).setUp()
        self.build_course()
        self.check_point = VerificationCheckpoint.objects.create(
            course_id=self.course.id, checkpoint_location=self.reverification_location
        )
        self.check_point.add_verification_attempt(SoftwareSecurePhotoVerification.objects.create(user=self.user))

        VerificationStatus.add_verification_status(
            checkpoint=self.check_point,
            user=self.user,
            status='submitted'
        )
        self.attempt = SoftwareSecurePhotoVerification.objects.filter(user=self.user)
        location_id = VerificationStatus.get_location_id(self.attempt)
        usage_key = UsageKey.from_string(location_id)
        redirect_url = get_redirect_url(self.course_key, usage_key.replace(course_key=self.course_key))
        self.request = RequestFactory().get('/url')
        self.course_link = self.request.build_absolute_uri(redirect_url)

    def test_approved_email_message(self):

        subject, body = _compose_message_reverification_email(
            self.course.id, self.user.id, self.reverification_location, "approved", self.request
        )

        self.assertIn(
            "We have successfully verified your identity for the {assessment} "
            "assessment in the {course_name} course.".format(
                assessment=self.assessment,
                course_name=self.course.display_name_with_default
            ),
            body
        )

        self.check_courseware_link_exists(body)
        self.assertIn("Re-verification Status", subject)

    def test_denied_email_message_with_valid_due_date_and_attempts_allowed(self):

        subject, body = _compose_message_reverification_email(
            self.course.id, self.user.id, self.reverification_location, "denied", self.request
        )

        self.assertIn(
            "We could not verify your identity for the {assessment} assessment "
            "in the {course_name} course. You have used "
            "{used_attempts} out of {allowed_attempts} attempts to "
            "verify your identity".format(
                course_name=self.course.display_name_with_default,
                assessment=self.assessment,
                used_attempts=1,
                allowed_attempts=self.allowed_attempts + 1
            ),
            body
        )

        self.assertIn(
            "You must verify your identity before the assessment "
            "closes on {due_date}".format(
                due_date=get_default_time_display(self.due_date)
            ),
            body
        )
        reverify_link = self.request.build_absolute_uri(self.re_verification_link)
        self.assertIn(
            "To try to verify your identity again, select the following link:",
            body
        )

        self.assertIn(reverify_link, body)
        self.assertIn("Re-verification Status", subject)

    def test_denied_email_message_with_due_date_and_no_attempts(self):
        """ Denied email message if due date is still open but user has no
            attempts available.
        """

        VerificationStatus.add_verification_status(
            checkpoint=self.check_point,
            user=self.user,
            status='submitted'
        )

        __, body = _compose_message_reverification_email(
            self.course.id, self.user.id, self.reverification_location, "denied", self.request
        )

        self.assertIn(
            "We could not verify your identity for the {assessment} assessment "
            "in the {course_name} course. You have used "
            "{used_attempts} out of {allowed_attempts} attempts to "
            "verify your identity, and verification is no longer "
            "possible".format(
                course_name=self.course.display_name_with_default,
                assessment=self.assessment,
                used_attempts=2,
                allowed_attempts=self.allowed_attempts + 1
            ),
            body
        )

        self.check_courseware_link_exists(body)

    def test_denied_email_message_with_close_verification_dates(self):
        # Due date given and expired
        return_value = datetime.now(tz=pytz.UTC) + timedelta(days=22)
        with patch.object(timezone, 'now', return_value=return_value):
            __, body = _compose_message_reverification_email(
                self.course.id, self.user.id, self.reverification_location, "denied", self.request
            )

            self.assertIn(
                "We could not verify your identity for the {assessment} assessment "
                "in the {course_name} course. You have used "
                "{used_attempts} out of {allowed_attempts} attempts to "
                "verify your identity, and verification is no longer "
                "possible".format(
                    course_name=self.course.display_name_with_default,
                    assessment=self.assessment,
                    used_attempts=1,
                    allowed_attempts=self.allowed_attempts + 1
                ),
                body
            )

    def test_check_num_queries(self):
        # Get the re-verification block to check the call made
        with check_mongo_calls(1):
            ver_block = modulestore().get_item(self.reverification.location)

        # Expect that the verification block is fetched
        self.assertIsNotNone(ver_block)

    def check_courseware_link_exists(self, body):
        """Checking courseware url and signature information of EDX"""
        self.assertIn(
            "To go to the courseware, select the following link:",
            body
        )
        self.assertIn(
            "{course_link}".format(
                course_link=self.course_link
            ),
            body
        )

        self.assertIn("Thanks,", body)
        self.assertIn(
            "The {platform_name} team".format(
                platform_name=settings.PLATFORM_NAME
            ),
            body
        )


class TestEmailMessageWithDefaultICRVBlock(ModuleStoreTestCase):
    """
    Test for In-course Re-verification
    """

    def build_course(self):
        """
        Build up a course tree with a Reverificaiton xBlock.
        """
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

        self.reverification = ItemFactory.create(
            parent=vertical,
            category='edx-reverification-block',
            display_name='Test Verification Block'
        )

        self.section_location = section.location
        self.subsection_location = subsection.location
        self.vertical_location = vertical.location
        self.reverification_location = unicode(self.reverification.location)
        self.assessment = self.reverification.related_assessment

        self.re_verification_link = reverse(
            'verify_student_incourse_reverify',
            args=(
                unicode(self.course_key),
                self.reverification_location
            )
        )

    def setUp(self):
        super(TestEmailMessageWithDefaultICRVBlock, self).setUp()

        self.build_course()
        self.check_point = VerificationCheckpoint.objects.create(
            course_id=self.course.id, checkpoint_location=self.reverification_location
        )
        self.check_point.add_verification_attempt(SoftwareSecurePhotoVerification.objects.create(user=self.user))
        self.attempt = SoftwareSecurePhotoVerification.objects.filter(user=self.user)
        self.request = RequestFactory().get('/url')

    def test_denied_email_message_with_no_attempt_allowed(self):

        VerificationStatus.add_verification_status(
            checkpoint=self.check_point,
            user=self.user,
            status='submitted'
        )

        __, body = _compose_message_reverification_email(
            self.course.id, self.user.id, self.reverification_location, "denied", self.request
        )

        self.assertIn(
            "We could not verify your identity for the {assessment} assessment "
            "in the {course_name} course. You have used "
            "{used_attempts} out of {allowed_attempts} attempts to "
            "verify your identity, and verification is no longer "
            "possible".format(
                course_name=self.course.display_name_with_default,
                assessment=self.assessment,
                used_attempts=1,
                allowed_attempts=1
            ),
            body
        )

    def test_error_on_compose_email(self):
        resp = _compose_message_reverification_email(
            self.course.id, self.user.id, self.reverification_location, "denied", True
        )
        self.assertIsNone(resp)

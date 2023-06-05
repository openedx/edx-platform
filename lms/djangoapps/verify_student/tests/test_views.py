# encoding: utf-8
"""
Tests of verify_student views.
"""

from datetime import timedelta
from uuid import uuid4

import ddt
import httpretty
import mock
import simplejson as json
import six
from bs4 import BeautifulSoup
from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now
from mock import Mock, patch
from opaque_keys.edx.locator import CourseLocator
from six.moves import zip
from waffle.testutils import override_switch

from common.test.utils import MockS3BotoMixin, XssTestMixin
from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.commerce.models import CommerceConfiguration
from lms.djangoapps.commerce.tests import TEST_API_URL, TEST_PAYMENT_DATA, TEST_PUBLIC_URL_ROOT
from lms.djangoapps.commerce.tests.mocks import mock_payment_processors
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification, VerificationDeadline
from lms.djangoapps.verify_student.views import PayAndVerifyView, checkout_with_ecommerce_service, render_to_response
from openedx.core.djangoapps.embargo.test_utils import restrict_course
from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme
from openedx.core.djangoapps.user_api.accounts.api import get_account_settings
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from common.djangoapps.util.testing import UrlResetMixin
from lms.djangoapps.verify_student.tests import TestVerificationBase
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


def mock_render_to_response(*args, **kwargs):
    return render_to_response(*args, **kwargs)


render_mock = Mock(side_effect=mock_render_to_response)

PAYMENT_DATA_KEYS = {'payment_processor_name', 'payment_page_url', 'payment_form_data'}


def _mock_payment_processors():
    """
    Mock out the payment processors endpoint, since we don't run ecommerce for unit tests here.
    Used in tests where ``mock_payment_processors`` can't be easily used, for example the whole
    test is an httpretty context or the mock may or may not be called depending on ddt parameters.
    """
    httpretty.register_uri(
        httpretty.GET,
        "{}/payment/processors/".format(TEST_API_URL),
        body=json.dumps(['foo', 'bar']),
        content_type="application/json",
    )


class StartView(TestCase):
    """
    This view is for the first time student is
    attempting a Photo Verification.
    """

    def start_url(self, course_id=""):
        return "/verify_student/{0}".format(six.moves.urllib.parse.quote(course_id))

    def test_start_new_verification(self):
        """
        Test the case where the user has no pending `PhotoVerificationAttempts`,
        but is just starting their first.
        """
        UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")

    def must_be_logged_in(self):
        self.assertHttpForbidden(self.client.get(self.start_url()))


@ddt.ddt
class TestPayAndVerifyView(UrlResetMixin, ModuleStoreTestCase, XssTestMixin, TestVerificationBase):
    """
    Tests for the payment and verification flow views.
    """
    MIN_PRICE = 12
    USERNAME = "test_user"
    PASSWORD = "test_password"

    NOW = now()
    NEXT_YEAR = 'next_year'
    DATES = {
        NEXT_YEAR: NOW + timedelta(days=360),
        None: None,
    }

    URLCONF_MODULES = ['openedx.core.djangoapps.embargo']

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        super(TestPayAndVerifyView, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result, msg="Could not log in")

    @ddt.data(
        ("verified", "verify_student_start_flow"),
        ("professional", "verify_student_start_flow"),
        ("verified", "verify_student_begin_flow"),
        ("professional", "verify_student_begin_flow")
    )
    @ddt.unpack
    def test_start_flow_not_verified(self, course_mode, payment_flow):
        course = self._create_course(course_mode)
        self._enroll(course.id)
        response = self._get_page(payment_flow, course.id)
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

    @httpretty.activate
    @override_settings(
        ECOMMERCE_API_URL=TEST_API_URL,
        ECOMMERCE_PUBLIC_URL_ROOT=TEST_PUBLIC_URL_ROOT
    )
    def test_start_flow_with_ecommerce(self):
        """Verify user gets redirected to ecommerce checkout when ecommerce checkout is enabled."""
        sku = 'TESTSKU'
        # When passing a SKU ecommerce api gets called.
        _mock_payment_processors()
        configuration = CommerceConfiguration.objects.create(checkout_on_ecommerce_service=True)
        checkout_page = configuration.basket_checkout_page
        checkout_page += "?utm_source=test"
        httpretty.register_uri(httpretty.GET, "{}{}".format(TEST_PUBLIC_URL_ROOT, checkout_page))

        course = self._create_course('verified', sku=sku)
        self._enroll(course.id)

        # Verify that utm params are included in the url used for redirect
        url_with_utm = 'http://www.example.com/basket/add/?utm_source=test&sku=TESTSKU'
        with mock.patch.object(EcommerceService, 'get_checkout_page_url', return_value=url_with_utm):
            response = self._get_page('verify_student_start_flow', course.id, expected_status_code=302)
        expected_page = '{}{}&sku={}'.format(TEST_PUBLIC_URL_ROOT, checkout_page, sku)
        self.assertRedirects(response, expected_page, fetch_redirect_response=False)

    @ddt.data(
        ("no-id-professional", "verify_student_start_flow"),
        ("no-id-professional", "verify_student_begin_flow")
    )
    @ddt.unpack
    def test_start_flow_with_no_id_professional(self, course_mode, payment_flow):
        course = self._create_course(course_mode)
        self._enroll(course.id)
        response = self._get_page(payment_flow, course.id)
        self._assert_displayed_mode(response, course_mode)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_messaging(response, PayAndVerifyView.FIRST_TIME_VERIFY_MSG)
        self._assert_requirements_displayed(response, [])

    def test_ab_testing_page(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        response = self._get_page("verify_student_begin_flow", course.id)
        self._assert_displayed_mode(response, "verified")
        self.assertContains(response, "Upgrade to a Verified Certificate")
        self.assertContains(response, "Before you upgrade to a certificate track,")
        self.assertContains(response, "To receive a certificate, you must also verify your identity")
        self.assertContains(response, "You will use your webcam to take a picture of")

    @ddt.data(
        ("expired", "verify_student_start_flow"),
        ("denied", "verify_student_begin_flow")
    )
    @ddt.unpack
    def test_start_flow_expired_or_denied_verification(self, verification_status, payment_flow):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        self._set_verification_status(verification_status)
        response = self._get_page(payment_flow, course.id)

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
        ("verified", "submitted", "verify_student_start_flow"),
        ("verified", "approved", "verify_student_start_flow"),
        ("verified", "error", "verify_student_start_flow"),
        ("professional", "submitted", "verify_student_start_flow"),
        ("no-id-professional", None, "verify_student_start_flow"),
        ("verified", "submitted", "verify_student_begin_flow"),
        ("verified", "approved", "verify_student_begin_flow"),
        ("verified", "error", "verify_student_begin_flow"),
        ("professional", "submitted", "verify_student_begin_flow"),
        ("no-id-professional", None, "verify_student_begin_flow"),

    )
    @ddt.unpack
    def test_start_flow_already_verified(self, course_mode, verification_status, payment_flow):
        course = self._create_course(course_mode)
        self._enroll(course.id)
        self._set_verification_status(verification_status)
        response = self._get_page(payment_flow, course.id)
        self._assert_displayed_mode(response, course_mode)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_messaging(response, PayAndVerifyView.FIRST_TIME_VERIFY_MSG)
        self._assert_requirements_displayed(response, [])

    @ddt.data(
        ("verified", "verify_student_start_flow"),
        ("professional", "verify_student_start_flow"),
        ("verified", "verify_student_begin_flow"),
        ("professional", "verify_student_begin_flow")
    )
    @ddt.unpack
    def test_start_flow_already_paid(self, course_mode, payment_flow):
        course = self._create_course(course_mode)
        self._enroll(course.id, course_mode)
        response = self._get_page(payment_flow, course.id)
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

    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_start_flow_not_enrolled(self, payment_flow):
        course = self._create_course("verified")
        self._set_verification_status("submitted")
        response = self._get_page(payment_flow, course.id)

        # This shouldn't happen if the student has been auto-enrolled,
        # but if they somehow end up on this page without enrolling,
        # treat them as if they need to pay
        response = self._get_page(payment_flow, course.id)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_requirements_displayed(response, [])

    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_start_flow_unenrolled(self, payment_flow):
        course = self._create_course("verified")
        self._set_verification_status("submitted")
        self._enroll(course.id, "verified")
        self._unenroll(course.id)

        # If unenrolled, treat them like they haven't paid at all
        # (we assume that they've gotten a refund or didn't pay initially)
        response = self._get_page(payment_flow, course.id)
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP
        )
        self._assert_requirements_displayed(response, [])

    @ddt.data(
        ("verified", "submitted", "verify_student_start_flow"),
        ("verified", "approved", "verify_student_start_flow"),
        ("professional", "submitted", "verify_student_start_flow"),
        ("verified", "submitted", "verify_student_begin_flow"),
        ("verified", "approved", "verify_student_begin_flow"),
        ("professional", "submitted", "verify_student_begin_flow")
    )
    @ddt.unpack
    def test_start_flow_already_verified_and_paid(self, course_mode, verification_status, payment_flow):
        course = self._create_course(course_mode)
        self._enroll(course.id, course_mode)
        self._set_verification_status(verification_status)
        response = self._get_page(
            payment_flow,
            course.id,
            expected_status_code=302
        )
        self._assert_redirects_to_dashboard(response)

    @with_comprehensive_theme("edx.org")
    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_pay_and_verify_hides_header_nav(self, payment_flow):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        response = self._get_page(payment_flow, course.id)

        # Verify that the header navigation links are hidden for the edx.org version
        self.assertNotContains(response, "How it Works")
        self.assertNotContains(response, "Find courses")
        self.assertNotContains(response, "Schools & Partners")

    def test_verify_now(self):
        # We've already paid, and now we're trying to verify
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        response = self._get_page('verify_student_verify_now', course.id)

        self._assert_messaging(response, PayAndVerifyView.VERIFY_NOW_MSG)
        self.assert_no_xss(response, '<script>alert("XSS")</script>')

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

    def test_verify_now_not_enrolled(self):
        course = self._create_course("verified")
        response = self._get_page("verify_student_verify_now", course.id, expected_status_code=302)
        self._assert_redirects_to_start_flow(response, course.id)

    def test_verify_now_unenrolled(self):
        course = self._create_course("verified")
        self._enroll(course.id, "verified")
        self._unenroll(course.id)
        response = self._get_page("verify_student_verify_now", course.id, expected_status_code=302)
        self._assert_redirects_to_start_flow(response, course.id)

    def test_verify_now_not_paid(self):
        course = self._create_course("verified")
        self._enroll(course.id)
        response = self._get_page("verify_student_verify_now", course.id, expected_status_code=302)
        self._assert_redirects_to_upgrade(response, course.id)

    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_payment_cannot_skip(self, payment_flow):
        """
         Simple test to verify that certain steps cannot be skipped. This test sets up
         a scenario where the user should be on the MAKE_PAYMENT_STEP, but is trying to
         skip it. Despite setting the parameter, the current step should still be
         MAKE_PAYMENT_STEP.
        """
        course = self._create_course("verified")
        response = self._get_page(
            payment_flow,
            course.id,
            skip_first_step=True
        )

        self._assert_messaging(response, PayAndVerifyView.FIRST_TIME_VERIFY_MSG)

        self.assert_no_xss(response, '<script>alert("XSS")</script>')

        # Expect that *all* steps are displayed,
        # but we start on the first verify step
        self._assert_steps_displayed(
            response,
            PayAndVerifyView.PAYMENT_STEPS + PayAndVerifyView.VERIFICATION_STEPS,
            PayAndVerifyView.MAKE_PAYMENT_STEP,
        )

    @ddt.data("verified", "professional")
    def test_upgrade(self, course_mode):
        course = self._create_course(course_mode)
        self._enroll(course.id)

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
        self.assert_no_xss(response, '<script>alert("XSS")</script>')

    def test_upgrade_already_verified(self):
        course = self._create_course("verified")
        self._enroll(course.id)
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
            'verify_student_begin_flow',
            'verify_student_verify_now',
            'verify_student_upgrade_and_verify',
        ]

        for page_name in pages:
            self._get_page(
                page_name,
                course.id,
                expected_status_code=404
            )

    @ddt.data(
        ([], "verify_student_start_flow"),
        (["no-id-professional", "professional"], "verify_student_start_flow"),
        (["honor", "audit"], "verify_student_start_flow"),
        ([], "verify_student_begin_flow"),
        (["no-id-professional", "professional"], "verify_student_begin_flow"),
        (["honor", "audit"], "verify_student_begin_flow"),
    )
    @ddt.unpack
    def test_no_id_professional_entry_point(self, modes_available, payment_flow):
        course = self._create_course(*modes_available)
        if "no-id-professional" in modes_available or "professional" in modes_available:
            self._get_page(payment_flow, course.id, expected_status_code=200)
        else:
            self._get_page(payment_flow, course.id, expected_status_code=404)

    @ddt.data(
        "verify_student_start_flow",
        "verify_student_begin_flow",
        "verify_student_verify_now",
        "verify_student_upgrade_and_verify",
    )
    def test_require_login(self, url_name):
        self.client.logout()
        course = self._create_course("verified")
        response = self._get_page(url_name, course.id, expected_status_code=302)

        original_url = reverse(url_name, kwargs={'course_id': six.text_type(course.id)})
        login_url = u"{login_url}?next={original_url}".format(
            login_url=reverse('signin_user'),
            original_url=original_url
        )
        self.assertRedirects(response, login_url)

    @ddt.data(
        "verify_student_start_flow",
        "verify_student_begin_flow",
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

    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_account_not_active(self, payment_flow):
        self.user.is_active = False
        self.user.save()
        course = self._create_course("verified")
        response = self._get_page(payment_flow, course.id)
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

    @override_switch(settings.DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH, active=True)
    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_disable_account_activation_requirement_flag_active(self, payment_flow):
        """
        Here we are validating that the activation requirement step is not
        being returned in the requirements response when the waffle flag is active
        """
        self.user.is_active = False
        self.user.save()
        course = self._create_course("verified")
        response = self._get_page(payment_flow, course.id)

        # Confirm that ID and webcam requirements are displayed,
        # and that activation requirement is hidden.
        self._assert_requirements_displayed(response, [
            PayAndVerifyView.PHOTO_ID_REQ,
            PayAndVerifyView.WEBCAM_REQ,
        ])

    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_no_contribution(self, payment_flow):
        # Do NOT specify a contribution for the course in a session var.
        course = self._create_course("verified")
        response = self._get_page(payment_flow, course.id)
        self._assert_contribution_amount(response, "")

    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_contribution_other_course(self, payment_flow):
        # Specify a contribution amount for another course in the session
        course = self._create_course("verified")
        other_course_id = CourseLocator(org="other", run="test", course="test")
        self._set_contribution("12.34", other_course_id)

        # Expect that the contribution amount is NOT pre-filled,
        response = self._get_page(payment_flow, course.id)
        self._assert_contribution_amount(response, "")

    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_contribution(self, payment_flow):
        # Specify a contribution amount for this course in the session
        course = self._create_course("verified")
        self._set_contribution("12.34", course.id)

        # Expect that the contribution amount is pre-filled,
        response = self._get_page(payment_flow, course.id)
        self._assert_contribution_amount(response, "12.34")

    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_verification_deadline(self, payment_flow):
        deadline = now() + timedelta(days=360)
        course = self._create_course("verified")

        # Set a deadline on the course mode AND on the verification deadline model.
        # This simulates the common case in which the upgrade deadline (course mode expiration)
        # and the verification deadline are the same.
        # NOTE: we used to use the course mode expiration datetime for BOTH of these deadlines,
        # before the VerificationDeadline model was introduced.
        self._set_deadlines(course.id, upgrade_deadline=deadline, verification_deadline=deadline)

        # Expect that the expiration date is set
        response = self._get_page(payment_flow, course.id)
        data = self._get_page_data(response)
        self.assertEqual(data['verification_deadline'], six.text_type(deadline))

    def test_course_mode_expired(self):
        deadline = now() + timedelta(days=-360)
        course = self._create_course("verified")

        # Set the upgrade deadline (course mode expiration) and verification deadline
        # to the same value.  This used to be the default when we used the expiration datetime
        # for BOTH values.
        self._set_deadlines(course.id, upgrade_deadline=deadline, verification_deadline=deadline)

        # Need to be enrolled
        self._enroll(course.id, "verified")

        # The course mode has expired, so expect an explanation
        # to the student that the deadline has passed
        response = self._get_page("verify_student_verify_now", course.id)
        self.assertContains(response, "verification deadline")
        self.assertContains(response, deadline)

    @ddt.data(NEXT_YEAR, None)
    def test_course_mode_expired_verification_deadline_in_future(self, verification_deadline):
        """Verify that student can not upgrade in expired course mode."""
        verification_deadline = self.DATES[verification_deadline]
        course_modes = ("verified", "credit")
        course = self._create_course(*course_modes)

        # Set the upgrade deadline of verified mode in the past, but the verification
        # deadline in the future.
        self._set_deadlines(
            course.id,
            upgrade_deadline=now() + timedelta(days=-360),
            verification_deadline=verification_deadline,
        )
        # Set the upgrade deadline for credit mode in future.
        self._set_deadlines(
            course.id,
            upgrade_deadline=now() + timedelta(days=360),
            verification_deadline=verification_deadline,
            mode_slug="credit"
        )

        # Try to pay or upgrade.
        # We should get an error message since the deadline has passed and did not allow
        # directly sale of credit mode.
        for page_name in ["verify_student_start_flow",
                          "verify_student_begin_flow",
                          "verify_student_upgrade_and_verify"]:
            response = self._get_page(page_name, course.id)
            self.assertContains(response, "Upgrade Deadline Has Passed")

        # Simulate paying for the course and enrolling
        self._enroll(course.id, "verified")

        # Enter the verification part of the flow
        # Expect that we are able to verify
        response = self._get_page("verify_student_verify_now", course.id)
        self.assertNotContains(response, "Verification is no longer available")

        data = self._get_page_data(response)
        self.assertEqual(data['message_key'], PayAndVerifyView.VERIFY_NOW_MSG)

        # Check that the mode selected is expired verified mode not the credit mode
        # because the direct enrollment to the credit mode is not allowed.
        self.assertEqual(data['course_mode_slug'], "verified")

        # Check that the verification deadline (rather than the upgrade deadline) is displayed
        if verification_deadline is not None:
            self.assertEqual(data["verification_deadline"], six.text_type(verification_deadline))
        else:
            self.assertEqual(data["verification_deadline"], "")

    def test_course_mode_not_expired_verification_deadline_passed(self):
        course = self._create_course("verified")

        # Set the upgrade deadline in the future
        # and the verification deadline in the past
        # We try not to discourage this with validation rules,
        # since it's a bad user experience
        # to purchase a verified track and then not be able to verify,
        # but if it happens we need to handle it gracefully.
        upgrade_deadline_in_future = now() + timedelta(days=360)
        verification_deadline_in_past = now() + timedelta(days=-360)
        self._set_deadlines(
            course.id,
            upgrade_deadline=upgrade_deadline_in_future,
            verification_deadline=verification_deadline_in_past,
        )

        # Enroll as verified (simulate purchasing the verified enrollment)
        self._enroll(course.id, "verified")

        # Even though the upgrade deadline is in the future,
        # the verification deadline has passed, so we should see an error
        # message when we go to verify.
        response = self._get_page("verify_student_verify_now", course.id)
        self.assertContains(response, "verification deadline")
        self.assertContains(response, verification_deadline_in_past)

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_embargo_restrict(self, payment_flow):
        course = self._create_course("verified")
        with restrict_course(course.id) as redirect_url:
            # Simulate that we're embargoed from accessing this
            # course based on our IP address.
            response = self._get_page(payment_flow, course.id, expected_status_code=302)
            self.assertRedirects(response, redirect_url)

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_embargo_allow(self, payment_flow):
        course = self._create_course("verified")
        self._get_page(payment_flow, course.id)

    def _create_course(self, *course_modes, **kwargs):
        """Create a new course with the specified course modes. """
        course = CourseFactory.create(display_name='<script>alert("XSS")</script>')

        if kwargs.get('course_start'):
            course.start = kwargs.get('course_start')
            modulestore().update_item(course, ModuleStoreEnum.UserID.test)

        mode_kwargs = {}
        if kwargs.get('sku'):
            mode_kwargs['sku'] = kwargs['sku']

        for course_mode in course_modes:
            min_price = (0 if course_mode in ["honor", "audit"] else self.MIN_PRICE)
            CourseModeFactory.create(
                course_id=course.id,
                mode_slug=course_mode,
                mode_display_name=course_mode,
                min_price=min_price,
                **mode_kwargs
            )

        return course

    def _enroll(self, course_key, mode=CourseMode.DEFAULT_MODE_SLUG):
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
            attempt = self.submit_attempt(attempt)

        if status in ["approved", "expired"]:
            attempt.approve()
        elif status == "denied":
            attempt.deny("Denied!")
        elif status == "error":
            attempt.system_error("Error!")

        if status == "expired":
            days_good_for = settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
            attempt.expiration_date = now() - timedelta(days=1)
            attempt.save()

    def _set_deadlines(self, course_key, upgrade_deadline=None, verification_deadline=None, mode_slug="verified"):
        """
        Set the upgrade and verification deadlines.

        Arguments:
            course_key (CourseKey): Identifier for the course.

        Keyword Arguments:

            upgrade_deadline (datetime): Datetime after which a user cannot
                upgrade to a verified mode.

            verification_deadline (datetime): Datetime after which a user cannot
                submit an initial verification attempt.

        """
        # Set the course mode expiration (same as the "upgrade" deadline)
        mode = CourseMode.objects.get(course_id=course_key, mode_slug=mode_slug)
        mode.expiration_datetime = upgrade_deadline
        mode.save()

        # Set the verification deadline
        VerificationDeadline.set_deadline(course_key, verification_deadline)

    def _set_contribution(self, amount, course_id):
        """Set the contribution amount pre-filled in a session var. """
        session = self.client.session
        session["donation_for_course"] = {
            six.text_type(course_id): amount
        }
        session.save()

    @httpretty.activate
    @override_settings(ECOMMERCE_API_URL=TEST_API_URL)
    def _get_page(self, url_name, course_key, expected_status_code=200, skip_first_step=False, assert_headers=False):
        """Retrieve one of the verification pages. """
        url = reverse(url_name, kwargs={"course_id": six.text_type(course_key)})

        if skip_first_step:
            url += "?skip-first-step=1"

        _mock_payment_processors()
        response = self.client.get(url)
        self.assertEqual(response.status_code, expected_status_code)

        if assert_headers:
            # ensure the mock api call was made.  NOTE: the following line
            # approximates the check - if the headers were empty it means
            # there was no last request.
            self.assertNotEqual(httpretty.last_request().headers, {})
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
        for req, displayed in six.iteritems(response_dict['requirements']):
            if req in requirements:
                self.assertTrue(displayed, msg=u"Expected '{req}' requirement to be displayed".format(req=req))
            else:
                self.assertFalse(displayed, msg=u"Expected '{req}' requirement to be hidden".format(req=req))

    def _assert_course_details(self, response, course_key, display_name, url):
        """Check the course information on the page. """
        response_dict = self._get_page_data(response)
        self.assertEqual(response_dict['course_key'], course_key)
        self.assertEqual(response_dict['course_name'], display_name)
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
        soup = BeautifulSoup(markup=response.content, features="lxml")
        pay_and_verify_div = soup.find(id="pay-and-verify-container")

        self.assertIsNot(
            pay_and_verify_div, None,
            msg=(
                "Could not load pay and verify flow data.  "
                "Maybe this isn't the pay and verify page?"
            )
        )

        return {
            'full_name': pay_and_verify_div['data-full-name'],
            'course_key': pay_and_verify_div['data-course-key'],
            'course_name': pay_and_verify_div['data-course-name'],
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
        url = reverse('verify_student_start_flow', kwargs={'course_id': six.text_type(course_id)})
        with mock_payment_processors():
            self.assertRedirects(response, url)

    def _assert_redirects_to_verify_start(self, response, course_id, status_code=302):
        """Check that the page redirects to the "verify later" part of the flow. """
        url = reverse('verify_student_verify_now', kwargs={'course_id': six.text_type(course_id)})
        with mock_payment_processors():
            self.assertRedirects(response, url, status_code)

    def _assert_redirects_to_upgrade(self, response, course_id):
        """Check that the page redirects to the "upgrade" part of the flow. """
        url = reverse('verify_student_upgrade_and_verify', kwargs={'course_id': six.text_type(course_id)})
        with mock_payment_processors():
            self.assertRedirects(response, url)

    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_course_upgrade_page_with_unicode_and_special_values_in_display_name(self, payment_flow):
        """Check the course information on the page. """
        mode_display_name = u"Introduction à l'astrophysique"
        course = CourseFactory.create(display_name=mode_display_name)
        for course_mode in [CourseMode.DEFAULT_MODE_SLUG, "verified"]:
            min_price = (self.MIN_PRICE if course_mode != CourseMode.DEFAULT_MODE_SLUG else 0)
            CourseModeFactory.create(
                course_id=course.id,
                mode_slug=course_mode,
                mode_display_name=mode_display_name,
                min_price=min_price
            )

        self._enroll(course.id)
        response_dict = self._get_page_data(self._get_page(payment_flow, course.id))

        self.assertEqual(response_dict['course_name'], mode_display_name)

    @ddt.data("verify_student_start_flow", "verify_student_begin_flow")
    def test_processors_api(self, payment_flow):
        """
        Check that when working with a product being processed by the
        ecommerce api, we correctly call to that api for the list of
        available payment processors.
        """
        # setting a nonempty sku on the course will a trigger calls to
        # the ecommerce api to get payment processors.
        course = self._create_course("verified", sku='nonempty-sku')
        self._enroll(course.id)

        # make the server request
        response = self._get_page(payment_flow, course.id, assert_headers=True)
        self.assertEqual(response.status_code, 200)


class CheckoutTestMixin(object):
    """
    Mixin implementing test methods that should behave identically regardless
    of which backend is used (currently only the ecommerce service).  Subclasses
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
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id, min_price=min_price, sku=self.make_sku())
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
        post_params.setdefault('processor', '')
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
            data = json.loads(response.content.decode('utf-8'))
            self.assertEqual(set(data.keys()), PAYMENT_DATA_KEYS)
        else:
            self.assertFalse(patched_create_order.called)

    def test_create_order(self, patched_create_order):
        # Create an order
        params = {
            'course_id': six.text_type(self.course.id),
            'contribution': 100,
        }
        self._assert_checked_out(params, patched_create_order, self.course.id, 'verified')

    def test_create_order_prof_ed(self, patched_create_order):
        # Create a prof ed course
        course = CourseFactory.create()
        CourseModeFactory.create(mode_slug="professional", course_id=course.id, min_price=10, sku=self.make_sku())
        # Create an order for a prof ed course
        params = {'course_id': six.text_type(course.id)}
        self._assert_checked_out(params, patched_create_order, course.id, 'professional')

    def test_create_order_no_id_professional(self, patched_create_order):
        # Create a no-id-professional ed course
        course = CourseFactory.create()
        CourseModeFactory.create(mode_slug="no-id-professional", course_id=course.id, min_price=10, sku=self.make_sku())
        # Create an order for a prof ed course
        params = {'course_id': six.text_type(course.id)}
        self._assert_checked_out(params, patched_create_order, course.id, 'no-id-professional')

    def test_create_order_for_multiple_paid_modes(self, patched_create_order):
        # Create a no-id-professional ed course
        course = CourseFactory.create()
        CourseModeFactory.create(mode_slug="no-id-professional", course_id=course.id, min_price=10, sku=self.make_sku())
        CourseModeFactory.create(mode_slug="professional", course_id=course.id, min_price=10, sku=self.make_sku())
        # Create an order for a prof ed course
        params = {'course_id': six.text_type(course.id)}
        # TODO jsa - is this the intended behavior?
        self._assert_checked_out(params, patched_create_order, course.id, 'no-id-professional')

    def test_create_order_bad_donation_amount(self, patched_create_order):
        # Create an order
        params = {
            'course_id': six.text_type(self.course.id),
            'contribution': '99.9'
        }
        self._assert_checked_out(params, patched_create_order, None, None, expected_status_code=400)

    def test_create_order_good_donation_amount(self, patched_create_order):
        # Create an order
        params = {
            'course_id': six.text_type(self.course.id),
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
        params = {'course_id': six.text_type(self.course.id), 'contribution': 100}
        response = self.client.post(reverse('verify_student_create_order'), params)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(patched_create_order.called)
        # ensure checkout args were correct
        args = self._get_checkout_args(patched_create_order)
        self.assertEqual(args['user'], self.user)
        self.assertEqual(args['course_key'], self.course.id)
        self.assertEqual(args['course_mode'].slug, 'verified')
        # ensure response data was correct
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {'foo': 'bar'})


@override_settings(ECOMMERCE_API_URL=TEST_API_URL)
@patch(
    'lms.djangoapps.verify_student.views.checkout_with_ecommerce_service',
    return_value=TEST_PAYMENT_DATA,
    autospec=True,
)
class TestCreateOrderEcommerceService(CheckoutTestMixin, ModuleStoreTestCase):
    """ Test view behavior when the ecommerce service is used. """

    def make_sku(self):
        """ Checkout is handled by the ecommerce service when the course mode's sku is nonempty. """
        return six.text_type(uuid4().hex)

    def _get_checkout_args(self, patched_create_order):
        """ Assuming patched_create_order was called, return a mapping containing the call arguments."""
        return dict(list(zip(('user', 'course_key', 'course_mode', 'processor'), patched_create_order.call_args[0])))


class TestCheckoutWithEcommerceService(ModuleStoreTestCase):
    """
    Ensures correct behavior in the function `checkout_with_ecommerce_service`.
    """

    @httpretty.activate
    @override_settings(ECOMMERCE_API_URL=TEST_API_URL)
    def test_create_basket(self):
        """
        Check that when working with a product being processed by the
        ecommerce api, we correctly call to that api to create a basket.
        """
        user = UserFactory.create(username="test-username")
        course_id = 'edX/test/test_run'
        course_mode = CourseModeFactory.create(course_id=course_id, sku="test-sku").to_tuple()
        expected_payment_data = {'foo': 'bar'}
        # mock out the payment processors endpoint
        httpretty.register_uri(
            httpretty.POST,
            "{}/baskets/".format(TEST_API_URL),
            body=json.dumps({'payment_data': expected_payment_data}),
            content_type="application/json",
        )

        with mock.patch('lms.djangoapps.verify_student.views.audit_log') as mock_audit_log:
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
        self.assertEqual(json.loads(httpretty.last_request().body.decode('utf-8')), {
            'products': [{'sku': 'test-sku'}],
            'checkout': True,
            'payment_processor_name': 'test-processor',
        })
        # Check the response
        self.assertEqual(actual_payment_data, expected_payment_data)


@ddt.ddt
@patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
class TestSubmitPhotosForVerification(MockS3BotoMixin, TestVerificationBase):
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

    def test_submit_photos_sends_confirmation_email(self):
        self._submit_photos(
            face_image=self.IMAGE_DATA,
            photo_id_image=self.IMAGE_DATA
        )
        self._assert_confirmation_email(True)

    def test_submit_photos_error_does_not_send_email(self):
        # Error because invalid parameters, so no confirmation email
        # should be sent.
        self._submit_photos(expected_status_code=400)
        self._assert_confirmation_email(False)

    # Disable auto-auth since we will be intercepting POST requests
    # to the verification service ourselves in this test.
    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': False})
    @override_settings(VERIFY_STUDENT={
        "SOFTWARE_SECURE": {
            "API_URL": "https://verify.example.com/submit/",
            "API_ACCESS_KEY": "dcf291b5572942f99adaab4c2090c006",
            "API_SECRET_KEY": "c392efdcc0354c5f922dc39844ec0dc7",
            "FACE_IMAGE_AES_KEY": "f82400259e3b4f88821cd89838758292",
            "RSA_PUBLIC_KEY": (
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDkgtz3fQdiXshy/RfOHkoHlhx/"
                "SSPZ+nNyE9JZXtwhlzsXjnu+e9GOuJzgh4kUqo73ePIG5FxVU+mnacvufq2cu1SOx"
                "lRYGyBK7qDf9Ym67I5gmmcNhbzdKcluAuDCPmQ4ecKpICQQldrDQ9HWDxwjbbcqpVB"
                "PYWkE1KrtypGThmcehLmabf6SPq1CTAGlXsHgUtbWCwV6mqR8yScV0nRLln0djLDm9d"
                "L8tIVFFVpAfBaYYh2Cm5EExQZjxyfjWd8P5H+8/l0pmK2jP7Hc0wuXJemIZbsdm+DSD"
                "FhCGY3AILGkMwr068dGRxfBtBy/U9U5W+nStvkDdMrSgQezS5+V test@example.com"
            ),
            "AWS_ACCESS_KEY": "c987c7efe35c403caa821f7328febfa1",
            "AWS_SECRET_KEY": "fc595fc657c04437bb23495d8fe64881",
            "S3_BUCKET": "test.example.com",
            "CERT_VERIFICATION_PATH": False,
        },
        "DAYS_GOOD_FOR": 10,
    })
    @httpretty.activate
    def test_submit_photos_for_reverification(self):
        httpretty.register_uri(
            httpretty.POST, settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["API_URL"],
            status=200, body={},
            content_type='application/json'
        )

        # Submit an initial verification attempt
        self._submit_photos(
            face_image=self.IMAGE_DATA + "4567",
            photo_id_image=self.IMAGE_DATA + "8910",
        )

        initial_data = self._get_post_data()

        # Submit a face photo for re-verification
        self._submit_photos(face_image=self.IMAGE_DATA + "1112")
        reverification_data = self._get_post_data()

        # Verify that the initial attempt sent the same ID photo as the reverification attempt
        self.assertEqual(initial_data["PhotoIDKey"], reverification_data["PhotoIDKey"])

        # Submit a new face photo and photo id for verification
        self._submit_photos(
            face_image=self.IMAGE_DATA + "9999",
            photo_id_image=self.IMAGE_DATA + "1111",
        )
        two_photo_reverification_data = self._get_post_data()

        # Verify that the initial attempt sent a new ID photo for the reverification attempt
        self.assertNotEqual(initial_data["PhotoIDKey"], two_photo_reverification_data["PhotoIDKey"])

    @ddt.data('face_image', 'photo_id_image')
    def test_invalid_image_data(self, invalid_param):
        params = {
            'face_image': self.IMAGE_DATA,
            'photo_id_image': self.IMAGE_DATA
        }
        params[invalid_param] = ""
        response = self._submit_photos(expected_status_code=400, **params)
        self.assertEqual(response.content.decode('utf-8'), "Image data is not valid.")

    def test_invalid_name(self):
        response = self._submit_photos(
            face_image=self.IMAGE_DATA,
            photo_id_image=self.IMAGE_DATA,
            full_name="",
            expected_status_code=400
        )
        self.assertEqual(response.content.decode('utf-8'), "Name must be at least 1 character long.")

    def test_missing_required_param(self):
        # Missing face image parameter
        params = {
            'photo_id_image': self.IMAGE_DATA
        }
        response = self._submit_photos(expected_status_code=400, **params)
        self.assertEqual(response.content.decode('utf-8'), "Missing required parameter face_image")

    def test_no_photo_id_and_no_initial_verification(self):
        # Submit face image data, but not photo ID data.
        # Since the user doesn't have an initial verification attempt, this should fail
        response = self._submit_photos(expected_status_code=400, face_image=self.IMAGE_DATA)
        self.assertEqual(
            response.content.decode('utf-8'),
            "Photo ID image is required if the user does not have an initial verification attempt."
        )

        # Create the initial verification attempt with some dummy
        # value set for field 'photo_id_key'
        self._submit_photos(
            face_image=self.IMAGE_DATA,
            photo_id_image=self.IMAGE_DATA,
        )
        attempt = SoftwareSecurePhotoVerification.objects.get(user=self.user)
        attempt.photo_id_key = "dummy_photo_id_key"
        attempt.save()

        # Now the request should succeed
        self._submit_photos(face_image=self.IMAGE_DATA)

    #
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

        with self.immediate_on_commit():
            response = self.client.post(url, params)
        self.assertEqual(response.status_code, expected_status_code)

        return response

    def _assert_confirmation_email(self, expect_email):
        """
        Check that a confirmation email was or was not sent.
        """
        if expect_email:
            # Verify that photo submission confirmation email was sent
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual('Thank you for submitting your photos!', mail.outbox[0].subject)
        else:
            # Verify that photo submission confirmation email was not sent
            self.assertEqual(len(mail.outbox), 0)

    def _assert_user_name(self, full_name):
        """Check the user's name.

        Arguments:
            full_name (unicode): The user's full name.

        Raises:
            AssertionError

        """
        request = RequestFactory().get('/url')
        request.user = self.user
        account_settings = get_account_settings(request)[0]
        self.assertEqual(account_settings['name'], full_name)

    def _get_post_data(self):
        """Retrieve POST data from the last request. """
        last_request = httpretty.last_request()
        return json.loads(last_request.body)


class TestPhotoVerificationResultsCallback(ModuleStoreTestCase, TestVerificationBase):
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

    def _assert_verification_approved_email(self):
        """Check that a verification approved email was sent."""
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Your édX ID verification was approved!')
        self.assertIn('Your édX ID verification photos have been approved', email.body)

    def _assert_verification_denied_email(self):
        """Check that a verification approved email was sent."""
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Your édX Verification Has Been Denied')
        self.assertIn('The photos you submitted for ID verification were not accepted', email.body)

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
        self.assertContains(response, 'Invalid JSON', status_code=400)

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
        self.assertContains(response, 'JSON should be dict', status_code=400)

    @patch(
        'lms.djangoapps.verify_student.ssencrypt.has_valid_signature',
        mock.Mock(side_effect=mocked_has_valid_signature)
    )
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
        self.assertContains(response, 'Access key invalid', status_code=400)

    @patch(
        'lms.djangoapps.verify_student.ssencrypt.has_valid_signature',
        mock.Mock(side_effect=mocked_has_valid_signature)
    )
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
        self.assertContains(response, 'edX ID Invalid-Id not found', status_code=400)

    @patch(
        'lms.djangoapps.verify_student.ssencrypt.has_valid_signature',
        mock.Mock(side_effect=mocked_has_valid_signature)
    )
    @patch('lms.djangoapps.verify_student.views.log.error')
    @patch('sailthru.sailthru_client.SailthruClient.send')
    def test_passed_status_template(self, _mock_sailthru_send, _mock_log_error):
        """
        Test for verification passed.
        """
        expiration_datetime = now() + timedelta(
            days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
        )
        verification = self.create_and_submit_attempt_for_user(self.user)
        verification.approve()
        verification.expiration_date = now()
        verification.expiry_email_date = now()
        verification.save()

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
        old_verification = SoftwareSecurePhotoVerification.objects.get(pk=verification.pk)
        self.assertEqual(attempt.status, u'approved')
        self.assertEqual(attempt.expiration_datetime.date(), expiration_datetime.date())
        self.assertIsNone(old_verification.expiry_email_date)
        self.assertEqual(response.content.decode('utf-8'), 'OK!')
        self._assert_verification_approved_email()

    @patch(
        'lms.djangoapps.verify_student.ssencrypt.has_valid_signature',
        mock.Mock(side_effect=mocked_has_valid_signature)
    )
    @patch('lms.djangoapps.verify_student.views.log.error')
    @patch('sailthru.sailthru_client.SailthruClient.send')
    def test_first_time_verification(self, mock_sailthru_send, mock_log_error):  # pylint: disable=unused-argument
        """
        Test for verification passed if the learner does not have any previous verification
        """
        expiration_datetime = now() + timedelta(
            days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
        )

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
        self.assertEqual(attempt.expiration_datetime.date(), expiration_datetime.date())
        self.assertEqual(response.content.decode('utf-8'), 'OK!')
        self._assert_verification_approved_email()

    @patch(
        'lms.djangoapps.verify_student.ssencrypt.has_valid_signature',
        mock.Mock(side_effect=mocked_has_valid_signature)
    )
    @patch('lms.djangoapps.verify_student.views.log.error')
    @patch('sailthru.sailthru_client.SailthruClient.send')
    def test_failed_status_template(self, _mock_sailthru_send, _mock_log_error):
        """
        Test for failed verification.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": 'FAIL',
            "Reason": [{"photoIdReasons": ["Not provided"]}],
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
        self.assertEqual(attempt.error_msg, u'[{"photoIdReasons": ["Not provided"]}]')
        self.assertEqual(response.content.decode('utf-8'), 'OK!')
        self._assert_verification_denied_email()

    @patch(
        'lms.djangoapps.verify_student.ssencrypt.has_valid_signature',
        mock.Mock(side_effect=mocked_has_valid_signature)
    )
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
        self.assertEqual(response.content.decode('utf-8'), 'OK!')

    @patch(
        'lms.djangoapps.verify_student.ssencrypt.has_valid_signature',
        mock.Mock(side_effect=mocked_has_valid_signature)
    )
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
        self.assertContains(response, 'Result Unknown not understood', status_code=400)


class TestReverifyView(TestVerificationBase):
    """
    Tests for the re-verification view.

    Re-verification occurs when a verification attempt is denied or expired,
    and the student is given the option to resubmit.
    """

    USERNAME = "shaftoe"
    PASSWORD = "detachment-2702"

    def setUp(self):
        super(TestReverifyView, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        success = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(success, msg="Could not log in")

    def test_reverify_view_can_do_initial_verification(self):
        """
        Test that a User can use re-verify link for initial verification.
        """
        self._assert_can_reverify()

    def test_reverify_view_can_reverify_denied(self):
        # User has a denied attempt, so can re-verify
        attempt = self.create_and_submit_attempt_for_user(self.user)
        attempt.deny("error")
        self._assert_can_reverify()

    def test_reverify_view_can_reverify_expired(self):
        # User has a verification attempt, but it's expired
        attempt = self.create_and_submit_attempt_for_user(self.user)
        attempt.approve()

        days_good_for = settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
        attempt.expiration_date = now() - timedelta(days=(days_good_for + 1))
        attempt.save()

        # Allow the student to re-verify
        self._assert_can_reverify()

    def test_reverify_view_can_reverify_pending(self):
        """ Test that the user can still re-verify even if the previous photo
        verification is in pending state.

        A photo verification is considered in pending state when the user has
        either submitted the photo verification (status in database: 'submitted')
        or photo verification submission failed (status in database: 'must_retry').
        """

        # User has submitted a verification attempt, but Software Secure has not yet responded
        self.create_and_submit_attempt_for_user(self.user)

        # Can re-verify because an attempt has already been submitted.
        self._assert_can_reverify()

    def test_reverify_view_cannot_reverify_approved(self):
        # Submitted attempt has been approved
        attempt = self.create_and_submit_attempt_for_user(self.user)
        attempt.approve()

        # Cannot re-verify because the user is already verified.
        self._assert_cannot_reverify()

    @override_settings(VERIFY_STUDENT={"DAYS_GOOD_FOR": 5, "EXPIRING_SOON_WINDOW": 10})
    def test_reverify_view_can_reverify_approved_expired_soon(self):
        """
        Verify that learner can submit photos if verification is set to expired soon.
        Verification will be good for next DAYS_GOOD_FOR (i.e here it is 5 days) days,
        and learner can submit photos if verification is set to expire in
        EXPIRING_SOON_WINDOW(i.e here it is 10 days) or less days.
        """
        attempt = self.create_and_submit_attempt_for_user(self.user)
        attempt.approve()

        # Can re-verify because verification is set to expired soon.
        self._assert_can_reverify()

    def _get_reverify_page(self):
        """
        Retrieve the re-verification page and return the response.
        """
        url = reverse("verify_student_reverify")
        return self.client.get(url)

    def _assert_can_reverify(self):
        """
        Check that the re-verification flow is rendered.
        """
        response = self._get_reverify_page()
        self.assertContains(response, "reverify-container")

    def _assert_cannot_reverify(self):
        """
        Check that the user is blocked from re-verifying.
        """
        response = self._get_reverify_page()
        self.assertContains(response, "reverify-blocked")

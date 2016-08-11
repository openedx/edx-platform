# -*- coding: utf-8 -*-
"""
Miscellaneous tests for the student app.
"""
import logging
import unittest
import ddt
from datetime import datetime, timedelta
from urlparse import urljoin

import pytz
from markupsafe import escape
from mock import Mock, patch
from nose.plugins.attrib import attr
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from pyquery import PyQuery as pq

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from course_modes.models import CourseMode
from student.models import (
    anonymous_id_for_user, user_by_anonymous_id, CourseEnrollment,
    unique_id_for_user, LinkedInAddToProfileConfiguration, UserAttribute
)
from student.views import (
    process_survey_link,
    _cert_info,
    complete_course_mode_info,
    _get_course_programs
)
from student.tests.factories import UserFactory, CourseModeFactory
from util.testing import EventTestMixin
from util.model_utils import USER_SETTINGS_CHANGED_EVENT_NAME
from xmodule.modulestore.tests.factories import CourseFactory, check_mongo_calls
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, ModuleStoreEnum

# These imports refer to lms djangoapps.
# Their testcases are only run under lms.
from bulk_email.models import Optout  # pylint: disable=import-error
from certificates.models import CertificateStatuses  # pylint: disable=import-error
from certificates.tests.factories import GeneratedCertificateFactory  # pylint: disable=import-error
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
import shoppingcart  # pylint: disable=import-error
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin

# Explicitly import the cache from ConfigurationModel so we can reset it after each test
from config_models.models import cache


log = logging.getLogger(__name__)


@ddt.ddt
class CourseEndingTest(TestCase):
    """Test things related to course endings: certificates, surveys, etc"""

    def test_process_survey_link(self):
        username = "fred"
        user = Mock(username=username)
        user_id = unique_id_for_user(user)
        link1 = "http://www.mysurvey.com"
        self.assertEqual(process_survey_link(link1, user), link1)

        link2 = "http://www.mysurvey.com?unique={UNIQUE_ID}"
        link2_expected = "http://www.mysurvey.com?unique={UNIQUE_ID}".format(UNIQUE_ID=user_id)
        self.assertEqual(process_survey_link(link2, user), link2_expected)

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': False})
    def test_cert_info(self):
        user = Mock(username="fred")
        survey_url = "http://a_survey.com"
        course = Mock(end_of_course_survey_url=survey_url, certificates_display_behavior='end')
        course_mode = 'honor'

        self.assertEqual(
            _cert_info(user, course, None, course_mode),
            {
                'status': 'processing',
                'show_disabled_download_button': False,
                'show_download_url': False,
                'show_survey_button': False,
                'can_unenroll': True,
            }
        )

        cert_status = {'status': 'unavailable'}
        self.assertEqual(
            _cert_info(user, course, cert_status, course_mode),
            {
                'status': 'processing',
                'show_disabled_download_button': False,
                'show_download_url': False,
                'show_survey_button': False,
                'mode': None,
                'linked_in_url': None,
                'can_unenroll': True,
            }
        )

        cert_status = {'status': 'generating', 'grade': '67', 'mode': 'honor'}
        self.assertEqual(
            _cert_info(user, course, cert_status, course_mode),
            {
                'status': 'generating',
                'show_disabled_download_button': True,
                'show_download_url': False,
                'show_survey_button': True,
                'survey_url': survey_url,
                'grade': '67',
                'mode': 'honor',
                'linked_in_url': None,
                'can_unenroll': False,
            }
        )

        download_url = 'http://s3.edx/cert'
        cert_status = {
            'status': 'downloadable', 'grade': '67',
            'download_url': download_url,
            'mode': 'honor'
        }

        self.assertEqual(
            _cert_info(user, course, cert_status, course_mode),
            {
                'status': 'ready',
                'show_disabled_download_button': False,
                'show_download_url': True,
                'download_url': download_url,
                'show_survey_button': True,
                'survey_url': survey_url,
                'grade': '67',
                'mode': 'honor',
                'linked_in_url': None,
                'can_unenroll': False,
            }
        )

        cert_status = {
            'status': 'notpassing', 'grade': '67',
            'download_url': download_url,
            'mode': 'honor'
        }
        self.assertEqual(
            _cert_info(user, course, cert_status, course_mode),
            {
                'status': 'notpassing',
                'show_disabled_download_button': False,
                'show_download_url': False,
                'show_survey_button': True,
                'survey_url': survey_url,
                'grade': '67',
                'mode': 'honor',
                'linked_in_url': None,
                'can_unenroll': True,
            }
        )

        # Test a course that doesn't have a survey specified
        course2 = Mock(end_of_course_survey_url=None)
        cert_status = {
            'status': 'notpassing', 'grade': '67',
            'download_url': download_url, 'mode': 'honor'
        }
        self.assertEqual(
            _cert_info(user, course2, cert_status, course_mode),
            {
                'status': 'notpassing',
                'show_disabled_download_button': False,
                'show_download_url': False,
                'show_survey_button': False,
                'grade': '67',
                'mode': 'honor',
                'linked_in_url': None,
                'can_unenroll': True,
            }
        )

        # test when the display is unavailable or notpassing, we get the correct results out
        course2.certificates_display_behavior = 'early_no_info'
        cert_status = {'status': 'unavailable'}
        self.assertEqual(_cert_info(user, course2, cert_status, course_mode), {})

        cert_status = {
            'status': 'notpassing', 'grade': '67',
            'download_url': download_url,
            'mode': 'honor'
        }
        self.assertEqual(_cert_info(user, course2, cert_status, course_mode), {})


@ddt.ddt
class DashboardTest(ModuleStoreTestCase):
    """
    Tests for dashboard utility functions
    """

    def setUp(self):
        super(DashboardTest, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username="jack", email="jack@fake.edx.org", password='test')
        self.client = Client()
        cache.clear()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def _check_verification_status_on(self, mode, value):
        """
        Check that the css class and the status message are in the dashboard html.
        """
        CourseModeFactory.create(mode_slug=mode, course_id=self.course.id)
        CourseEnrollment.enroll(self.user, self.course.location.course_key, mode=mode)

        if mode == 'verified':
            # Simulate a successful verification attempt
            attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
            attempt.mark_ready()
            attempt.submit()
            attempt.approve()

        response = self.client.get(reverse('dashboard'))
        if mode in ['professional', 'no-id-professional']:
            self.assertContains(response, 'class="course professional"')
        else:
            self.assertContains(response, 'class="course {0}"'.format(mode))
        self.assertContains(response, value)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_VERIFIED_CERTIFICATES': True})
    def test_verification_status_visible(self):
        """
        Test that the certificate verification status for courses is visible on the dashboard.
        """
        self.client.login(username="jack", password="test")
        self._check_verification_status_on('verified', 'You&#39;re enrolled as a verified student')
        self._check_verification_status_on('honor', 'You&#39;re enrolled as an honor code student')
        self._check_verification_status_off('audit', '')
        self._check_verification_status_on('professional', 'You&#39;re enrolled as a professional education student')
        self._check_verification_status_on(
            'no-id-professional',
            'You&#39;re enrolled as a professional education student',
        )

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def _check_verification_status_off(self, mode, value):
        """
        Check that the css class and the status message are not in the dashboard html.
        """
        CourseModeFactory.create(mode_slug=mode, course_id=self.course.id)
        CourseEnrollment.enroll(self.user, self.course.location.course_key, mode=mode)

        if mode == 'verified':
            # Simulate a successful verification attempt
            attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
            attempt.mark_ready()
            attempt.submit()
            attempt.approve()

        response = self.client.get(reverse('dashboard'))

        if mode == 'audit':
            # Audit mode does not have a banner.  Assert no banner element.
            self.assertEqual(pq(response.content)(".sts-enrollment").length, 0)
        else:
            self.assertNotContains(response, "class=\"course {0}\"".format(mode))
            self.assertNotContains(response, value)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_VERIFIED_CERTIFICATES': False})
    def test_verification_status_invisible(self):
        """
        Test that the certificate verification status for courses is not visible on the dashboard
        if the verified certificates setting is off.
        """
        self.client.login(username="jack", password="test")
        self._check_verification_status_off('verified', 'You\'re enrolled as a verified student')
        self._check_verification_status_off('honor', 'You\'re enrolled as an honor code student')
        self._check_verification_status_off('audit', '')

    def test_course_mode_info(self):
        verified_mode = CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='verified',
            mode_display_name='Verified',
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=1)
        )
        enrollment = CourseEnrollment.enroll(self.user, self.course.id)
        course_mode_info = complete_course_mode_info(self.course.id, enrollment)
        self.assertTrue(course_mode_info['show_upsell'])
        self.assertEquals(course_mode_info['days_for_upsell'], 1)

        verified_mode.expiration_datetime = datetime.now(pytz.UTC) + timedelta(days=-1)
        verified_mode.save()
        course_mode_info = complete_course_mode_info(self.course.id, enrollment)
        self.assertFalse(course_mode_info['show_upsell'])
        self.assertIsNone(course_mode_info['days_for_upsell'])

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @patch('courseware.views.index.log.warning')
    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_blocked_course_scenario(self, log_warning):

        self.client.login(username="jack", password="test")

        #create testing invoice 1
        sale_invoice_1 = shoppingcart.models.Invoice.objects.create(
            total_amount=1234.32, company_name='Test1', company_contact_name='Testw',
            company_contact_email='test1@test.com', customer_reference_number='2Fwe23S',
            recipient_name='Testw_1', recipient_email='test2@test.com', internal_reference="A",
            course_id=self.course.id, is_valid=False
        )
        invoice_item = shoppingcart.models.CourseRegistrationCodeInvoiceItem.objects.create(
            invoice=sale_invoice_1,
            qty=1,
            unit_price=1234.32,
            course_id=self.course.id
        )
        course_reg_code = shoppingcart.models.CourseRegistrationCode(
            code="abcde",
            course_id=self.course.id,
            created_by=self.user,
            invoice=sale_invoice_1,
            invoice_item=invoice_item,
            mode_slug=CourseMode.DEFAULT_MODE_SLUG
        )
        course_reg_code.save()

        cart = shoppingcart.models.Order.get_cart_for_user(self.user)
        shoppingcart.models.PaidCourseRegistration.add_to_order(cart, self.course.id)
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': course_reg_code.code})
        self.assertEqual(resp.status_code, 200)

        redeem_url = reverse('register_code_redemption', args=[course_reg_code.code])
        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertIn('Activate Course Enrollment', response.content)

        #now activate the user by enrolling him/her to the course
        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)
        response = self.client.get(reverse('dashboard'))
        self.assertIn('You can no longer access this course because payment has not yet been received', response.content)
        optout_object = Optout.objects.filter(user=self.user, course_id=self.course.id)
        self.assertEqual(len(optout_object), 1)

        # Direct link to course redirect to user dashboard
        self.client.get(reverse('courseware', kwargs={"course_id": self.course.id.to_deprecated_string()}))
        log_warning.assert_called_with(
            u'User %s cannot access the course %s because payment has not yet been received',
            self.user,
            unicode(self.course.id),
        )

        # Now re-validating the invoice
        invoice = shoppingcart.models.Invoice.objects.get(id=sale_invoice_1.id)
        invoice.is_valid = True
        invoice.save()

        response = self.client.get(reverse('dashboard'))
        self.assertNotIn('You can no longer access this course because payment has not yet been received', response.content)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_linked_in_add_to_profile_btn_not_appearing_without_config(self):
        # Without linked-in config don't show Add Certificate to LinkedIn button
        self.client.login(username="jack", password="test")

        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='verified',
            mode_display_name='verified',
            expiration_datetime=datetime.now(pytz.UTC) - timedelta(days=1)
        )

        CourseEnrollment.enroll(self.user, self.course.id, mode='honor')

        self.course.start = datetime.now(pytz.UTC) - timedelta(days=2)
        self.course.end = datetime.now(pytz.UTC) - timedelta(days=1)
        self.course.display_name = u"Omega"
        self.course = self.update_course(self.course, self.user.id)

        download_url = 'www.edx.org'
        GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='honor',
            grade='67',
            download_url=download_url
        )
        response = self.client.get(reverse('dashboard'))

        self.assertEquals(response.status_code, 200)
        self.assertNotIn('Add Certificate to LinkedIn', response.content)

        response_url = 'http://www.linkedin.com/profile/add?_ed='
        self.assertNotContains(response, escape(response_url))

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': False})
    def test_linked_in_add_to_profile_btn_with_certificate(self):
        # If user has a certificate with valid linked-in config then Add Certificate to LinkedIn button
        # should be visible. and it has URL value with valid parameters.
        self.client.login(username="jack", password="test")
        LinkedInAddToProfileConfiguration(
            company_identifier='0_mC_o2MizqdtZEmkVXjH4eYwMj4DnkCWrZP_D9',
            enabled=True
        ).save()

        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='verified',
            mode_display_name='verified',
            expiration_datetime=datetime.now(pytz.UTC) - timedelta(days=1)
        )

        CourseEnrollment.enroll(self.user, self.course.id, mode='honor')

        self.course.start = datetime.now(pytz.UTC) - timedelta(days=2)
        self.course.end = datetime.now(pytz.UTC) - timedelta(days=1)
        self.course.display_name = u"Omega"
        self.course = self.update_course(self.course, self.user.id)

        download_url = 'www.edx.org'
        GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='honor',
            grade='67',
            download_url=download_url
        )
        response = self.client.get(reverse('dashboard'))

        self.assertEquals(response.status_code, 200)
        self.assertIn('Add Certificate to LinkedIn', response.content)

        expected_url = (
            'http://www.linkedin.com/profile/add'
            '?_ed=0_mC_o2MizqdtZEmkVXjH4eYwMj4DnkCWrZP_D9&'
            'pfCertificationName=edX+Honor+Code+Certificate+for+Omega&'
            'pfCertificationUrl=www.edx.org&'
            'source=o'
        )
        self.assertContains(response, escape(expected_url))

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_dashboard_metadata_caching(self, modulestore_type):
        """
        Check that the student dashboard makes use of course metadata caching.

        After creating a course, that course's metadata should be cached as a
        CourseOverview. The student dashboard should never have to make calls to
        the modulestore.

        Arguments:
            modulestore_type (ModuleStoreEnum.Type): Type of modulestore to create
                test course in.

        Note to future developers:
            If you break this test so that the "check_mongo_calls(0)" fails,
            please do NOT change it to "check_mongo_calls(n>1)". Instead, change
            your code to not load courses from the module store. This may
            involve adding fields to CourseOverview so that loading a full
            CourseDescriptor isn't necessary.
        """
        # Create a course and log in the user.
        # Creating a new course will trigger a publish event and the course will be cached
        test_course = CourseFactory.create(default_store=modulestore_type, emit_signals=True)
        self.client.login(username="jack", password="test")

        with check_mongo_calls(0):
            CourseEnrollment.enroll(self.user, test_course.id)

        # Subsequent requests will only result in SQL queries to load the
        # CourseOverview object that has been created.
        with check_mongo_calls(0):
            response_1 = self.client.get(reverse('dashboard'))
            self.assertEquals(response_1.status_code, 200)
            response_2 = self.client.get(reverse('dashboard'))
            self.assertEquals(response_2.status_code, 200)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_dashboard_header_nav_has_find_courses(self):
        self.client.login(username="jack", password="test")
        response = self.client.get(reverse("dashboard"))

        # "Explore courses" is shown in the side panel
        self.assertContains(response, "Explore courses")

        # But other links are hidden in the navigation
        self.assertNotContains(response, "How it Works")
        self.assertNotContains(response, "Schools & Partners")

    def test_course_mode_info_with_honor_enrollment(self):
        """It will be true only if enrollment mode is honor and course has verified mode."""
        course_mode_info = self._enrollment_with_complete_course('honor')
        self.assertTrue(course_mode_info['show_upsell'])
        self.assertEquals(course_mode_info['days_for_upsell'], 1)

    @ddt.data('verified', 'credit')
    def test_course_mode_info_with_different_enrollments(self, enrollment_mode):
        """If user enrollment mode is either verified or credit then show_upsell
        will be always false.
        """
        course_mode_info = self._enrollment_with_complete_course(enrollment_mode)
        self.assertFalse(course_mode_info['show_upsell'])
        self.assertIsNone(course_mode_info['days_for_upsell'])

    def _enrollment_with_complete_course(self, enrollment_mode):
        """"Dry method for course enrollment."""
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='verified',
            mode_display_name='Verified',
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=1)
        )
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode=enrollment_mode)
        return complete_course_mode_info(self.course.id, enrollment)


class UserSettingsEventTestMixin(EventTestMixin):
    """
    Mixin for verifying that user setting events were emitted during a test.
    """
    def setUp(self):
        super(UserSettingsEventTestMixin, self).setUp('util.model_utils.tracker')

    def assert_user_setting_event_emitted(self, **kwargs):
        """
        Helper method to assert that we emit the expected user settings events.

        Expected settings are passed in via `kwargs`.
        """
        if 'truncated' not in kwargs:
            kwargs['truncated'] = []
        self.assert_event_emitted(
            USER_SETTINGS_CHANGED_EVENT_NAME,
            table=self.table,
            user_id=self.user.id,
            **kwargs
        )


class EnrollmentEventTestMixin(EventTestMixin):
    """ Mixin with assertions for validating enrollment events. """
    def setUp(self):
        super(EnrollmentEventTestMixin, self).setUp('student.models.tracker')

    def assert_enrollment_mode_change_event_was_emitted(self, user, course_key, mode):
        """Ensures an enrollment mode change event was emitted"""
        self.mock_tracker.emit.assert_called_once_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.mode_changed',
            {
                'course_id': course_key.to_deprecated_string(),
                'user_id': user.pk,
                'mode': mode
            }
        )
        self.mock_tracker.reset_mock()

    def assert_enrollment_event_was_emitted(self, user, course_key):
        """Ensures an enrollment event was emitted since the last event related assertion"""
        self.mock_tracker.emit.assert_called_once_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.activated',
            {
                'course_id': course_key.to_deprecated_string(),
                'user_id': user.pk,
                'mode': CourseMode.DEFAULT_MODE_SLUG
            }
        )
        self.mock_tracker.reset_mock()

    def assert_unenrollment_event_was_emitted(self, user, course_key):
        """Ensures an unenrollment event was emitted since the last event related assertion"""
        self.mock_tracker.emit.assert_called_once_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.deactivated',
            {
                'course_id': course_key.to_deprecated_string(),
                'user_id': user.pk,
                'mode': CourseMode.DEFAULT_MODE_SLUG
            }
        )
        self.mock_tracker.reset_mock()


class EnrollInCourseTest(EnrollmentEventTestMixin, TestCase):
    """Tests enrolling and unenrolling in courses."""

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_enrollment(self):
        user = User.objects.create_user("joe", "joe@joe.com", "password")
        course_id = SlashSeparatedCourseKey("edX", "Test101", "2013")
        course_id_partial = SlashSeparatedCourseKey("edX", "Test101", None)

        # Test basic enrollment
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assertFalse(CourseEnrollment.is_enrolled_by_partial(user, course_id_partial))
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assertTrue(CourseEnrollment.is_enrolled_by_partial(user, course_id_partial))
        self.assert_enrollment_event_was_emitted(user, course_id)

        # Enrolling them again should be harmless
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assertTrue(CourseEnrollment.is_enrolled_by_partial(user, course_id_partial))
        self.assert_no_events_were_emitted()

        # Now unenroll the user
        CourseEnrollment.unenroll(user, course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assertFalse(CourseEnrollment.is_enrolled_by_partial(user, course_id_partial))
        self.assert_unenrollment_event_was_emitted(user, course_id)

        # Unenrolling them again should also be harmless
        CourseEnrollment.unenroll(user, course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assertFalse(CourseEnrollment.is_enrolled_by_partial(user, course_id_partial))
        self.assert_no_events_were_emitted()

        # The enrollment record should still exist, just be inactive
        enrollment_record = CourseEnrollment.objects.get(
            user=user,
            course_id=course_id
        )
        self.assertFalse(enrollment_record.is_active)

        # Make sure mode is updated properly if user unenrolls & re-enrolls
        enrollment = CourseEnrollment.enroll(user, course_id, "verified")
        self.assertEquals(enrollment.mode, "verified")
        CourseEnrollment.unenroll(user, course_id)
        enrollment = CourseEnrollment.enroll(user, course_id, "audit")
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assertEquals(enrollment.mode, "audit")

    def test_enrollment_non_existent_user(self):
        # Testing enrollment of newly unsaved user (i.e. no database entry)
        user = User(username="rusty", email="rusty@fake.edx.org")
        course_id = SlashSeparatedCourseKey("edX", "Test101", "2013")

        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Unenroll does nothing
        CourseEnrollment.unenroll(user, course_id)
        self.assert_no_events_were_emitted()

        # Implicit save() happens on new User object when enrolling, so this
        # should still work
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_enrollment_event_was_emitted(user, course_id)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_enrollment_by_email(self):
        user = User.objects.create(username="jack", email="jack@fake.edx.org")
        course_id = SlashSeparatedCourseKey("edX", "Test101", "2013")

        CourseEnrollment.enroll_by_email("jack@fake.edx.org", course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_enrollment_event_was_emitted(user, course_id)

        # This won't throw an exception, even though the user is not found
        self.assertIsNone(
            CourseEnrollment.enroll_by_email("not_jack@fake.edx.org", course_id)
        )
        self.assert_no_events_were_emitted()

        self.assertRaises(
            User.DoesNotExist,
            CourseEnrollment.enroll_by_email,
            "not_jack@fake.edx.org",
            course_id,
            ignore_errors=False
        )
        self.assert_no_events_were_emitted()

        # Now unenroll them by email
        CourseEnrollment.unenroll_by_email("jack@fake.edx.org", course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_unenrollment_event_was_emitted(user, course_id)

        # Harmless second unenroll
        CourseEnrollment.unenroll_by_email("jack@fake.edx.org", course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_no_events_were_emitted()

        # Unenroll on non-existent user shouldn't throw an error
        CourseEnrollment.unenroll_by_email("not_jack@fake.edx.org", course_id)
        self.assert_no_events_were_emitted()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_enrollment_multiple_classes(self):
        user = User(username="rusty", email="rusty@fake.edx.org")
        course_id1 = SlashSeparatedCourseKey("edX", "Test101", "2013")
        course_id2 = SlashSeparatedCourseKey("MITx", "6.003z", "2012")

        CourseEnrollment.enroll(user, course_id1)
        self.assert_enrollment_event_was_emitted(user, course_id1)
        CourseEnrollment.enroll(user, course_id2)
        self.assert_enrollment_event_was_emitted(user, course_id2)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id1))
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id2))

        CourseEnrollment.unenroll(user, course_id1)
        self.assert_unenrollment_event_was_emitted(user, course_id1)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id1))
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id2))

        CourseEnrollment.unenroll(user, course_id2)
        self.assert_unenrollment_event_was_emitted(user, course_id2)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id1))
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id2))

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_activation(self):
        user = User.objects.create(username="jack", email="jack@fake.edx.org")
        course_id = SlashSeparatedCourseKey("edX", "Test101", "2013")
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Creating an enrollment doesn't actually enroll a student
        # (calling CourseEnrollment.enroll() would have)
        enrollment = CourseEnrollment.get_or_create_enrollment(user, course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_no_events_were_emitted()

        # Until you explicitly activate it
        enrollment.activate()
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_enrollment_event_was_emitted(user, course_id)

        # Activating something that's already active does nothing
        enrollment.activate()
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_no_events_were_emitted()

        # Now deactive
        enrollment.deactivate()
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_unenrollment_event_was_emitted(user, course_id)

        # Deactivating something that's already inactive does nothing
        enrollment.deactivate()
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_no_events_were_emitted()

        # A deactivated enrollment should be activated if enroll() is called
        # for that user/course_id combination
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_enrollment_event_was_emitted(user, course_id)

    def test_change_enrollment_modes(self):
        user = User.objects.create(username="justin", email="jh@fake.edx.org")
        course_id = SlashSeparatedCourseKey("edX", "Test101", "2013")

        CourseEnrollment.enroll(user, course_id, "audit")
        self.assert_enrollment_event_was_emitted(user, course_id)

        CourseEnrollment.enroll(user, course_id, "honor")
        self.assert_enrollment_mode_change_event_was_emitted(user, course_id, "honor")

        # same enrollment mode does not emit an event
        CourseEnrollment.enroll(user, course_id, "honor")
        self.assert_no_events_were_emitted()

        CourseEnrollment.enroll(user, course_id, "audit")
        self.assert_enrollment_mode_change_event_was_emitted(user, course_id, "audit")


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ChangeEnrollmentViewTest(ModuleStoreTestCase):
    """Tests the student.views.change_enrollment view"""

    def setUp(self):
        super(ChangeEnrollmentViewTest, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(password='secret')
        self.client.login(username=self.user.username, password='secret')
        self.url = reverse('change_enrollment')

    def _enroll_through_view(self, course):
        """ Enroll a student in a course. """
        response = self.client.post(
            reverse('change_enrollment'), {
                'course_id': course.id.to_deprecated_string(),
                'enrollment_action': 'enroll'
            }
        )
        return response

    def test_enroll_as_default(self):
        """Tests that a student can successfully enroll through this view"""
        response = self._enroll_through_view(self.course)
        self.assertEqual(response.status_code, 200)
        enrollment_mode, is_active = CourseEnrollment.enrollment_mode_for_user(
            self.user, self.course.id
        )
        self.assertTrue(is_active)
        self.assertEqual(enrollment_mode, CourseMode.DEFAULT_MODE_SLUG)

    def test_cannot_enroll_if_already_enrolled(self):
        """
        Tests that a student will not be able to enroll through this view if
        they are already enrolled in the course
        """
        CourseEnrollment.enroll(self.user, self.course.id)
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        # now try to enroll that student
        response = self._enroll_through_view(self.course)
        self.assertEqual(response.status_code, 400)

    def test_change_to_default_if_verified(self):
        """
        Tests that a student that is a currently enrolled verified student cannot
        accidentally change their enrollment mode
        """
        CourseEnrollment.enroll(self.user, self.course.id, mode=u'verified')
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        # now try to enroll the student in the default mode:
        response = self._enroll_through_view(self.course)
        self.assertEqual(response.status_code, 400)
        enrollment_mode, is_active = CourseEnrollment.enrollment_mode_for_user(
            self.user, self.course.id
        )
        self.assertTrue(is_active)
        self.assertEqual(enrollment_mode, u'verified')

    def test_change_to_default_if_verified_not_active(self):
        """
        Tests that one can renroll for a course if one has already unenrolled
        """
        # enroll student
        CourseEnrollment.enroll(self.user, self.course.id, mode=u'verified')
        # now unenroll student:
        CourseEnrollment.unenroll(self.user, self.course.id)
        # check that they are verified but inactive
        enrollment_mode, is_active = CourseEnrollment.enrollment_mode_for_user(
            self.user, self.course.id
        )
        self.assertFalse(is_active)
        self.assertEqual(enrollment_mode, u'verified')
        # now enroll them through the view:
        response = self._enroll_through_view(self.course)
        self.assertEqual(response.status_code, 200)
        enrollment_mode, is_active = CourseEnrollment.enrollment_mode_for_user(
            self.user, self.course.id
        )
        self.assertTrue(is_active)
        self.assertEqual(enrollment_mode, CourseMode.DEFAULT_MODE_SLUG)


class AnonymousLookupTable(ModuleStoreTestCase):
    """
    Tests for anonymous_id_functions
    """
    def setUp(self):
        super(AnonymousLookupTable, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory()
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor Code',
        )
        patcher = patch('student.models.tracker')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_for_unregistered_user(self):  # same path as for logged out user
        self.assertEqual(None, anonymous_id_for_user(AnonymousUser(), self.course.id))
        self.assertIsNone(user_by_anonymous_id(None))

    def test_roundtrip_for_logged_user(self):
        CourseEnrollment.enroll(self.user, self.course.id)
        anonymous_id = anonymous_id_for_user(self.user, self.course.id)
        real_user = user_by_anonymous_id(anonymous_id)
        self.assertEqual(self.user, real_user)
        self.assertEqual(anonymous_id, anonymous_id_for_user(self.user, self.course.id, save=False))

    def test_roundtrip_with_unicode_course_id(self):
        course2 = CourseFactory.create(display_name=u"Omega Course Ω")
        CourseEnrollment.enroll(self.user, course2.id)
        anonymous_id = anonymous_id_for_user(self.user, course2.id)
        real_user = user_by_anonymous_id(anonymous_id)
        self.assertEqual(self.user, real_user)
        self.assertEqual(anonymous_id, anonymous_id_for_user(self.user, course2.id, save=False))


# TODO: Clean up these tests so that they use program factories and don't mention XSeries!
@attr(shard=3)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@ddt.ddt
class DashboardTestXSeriesPrograms(ModuleStoreTestCase, ProgramsApiConfigMixin):
    """
    Tests for dashboard for xseries program courses. Enroll student into
    programs and then try different combinations to see xseries upsell
    messages are appearing.
    """
    def setUp(self):
        super(DashboardTestXSeriesPrograms, self).setUp()

        self.user = UserFactory.create(username="jack", email="jack@fake.edx.org", password='test')
        self.course_1 = CourseFactory.create()
        self.course_2 = CourseFactory.create()
        self.course_3 = CourseFactory.create()
        self.program_name = 'Testing Program'
        self.category = 'XSeries'

        CourseModeFactory.create(
            course_id=self.course_1.id,
            mode_slug='verified',
            mode_display_name='Verified',
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=1)
        )
        self.client = Client()
        cache.clear()

    def _create_program_data(self, data):
        """Dry method to create testing programs data."""
        programs = {}
        _id = 0

        for course, program_status in data:
            programs[unicode(course)] = [{
                'id': _id,
                'category': self.category,
                'organization': {'display_name': 'Test Organization 1', 'key': 'edX'},
                'marketing_slug': 'fake-marketing-slug-xseries-1',
                'status': program_status,
                'course_codes': [
                    {
                        'display_name': 'Demo XSeries Program 1',
                        'key': unicode(course),
                        'run_modes': [{'sku': '', 'mode_slug': 'ABC', 'course_key': unicode(course)}]
                    },
                    {
                        'display_name': 'Demo XSeries Program 2',
                        'key': 'edx/demo/course_2',
                        'run_modes': [{'sku': '', 'mode_slug': 'ABC', 'course_key': 'edx/demo/course_2'}]
                    },
                    {
                        'display_name': 'Demo XSeries Program 3',
                        'key': 'edx/demo/course_3',
                        'run_modes': [{'sku': '', 'mode_slug': 'ABC', 'course_key': 'edx/demo/course_3'}]
                    }
                ],
                'subtitle': 'sub',
                'name': self.program_name
            }]

            _id += 1

        return programs

    @ddt.data(
        ('active', [{'sku': ''}, {'sku': ''}, {'sku': ''}, {'sku': ''}], 'marketing-slug-1'),
        ('active', [{'sku': ''}, {'sku': ''}, {'sku': ''}], 'marketing-slug-2'),
        ('active', [], ''),
        ('unpublished', [{'sku': ''}, {'sku': ''}, {'sku': ''}, {'sku': ''}], 'marketing-slug-3'),
    )
    @ddt.unpack
    def test_get_xseries_programs_method(self, program_status, course_codes, marketing_slug):
        """Verify that program data is parsed correctly for a given course"""
        with patch('student.views.get_programs_for_dashboard') as mock_data:
            mock_data.return_value = {
                u'edx/demox/Run_1': [{
                    'id': 0,
                    'category': self.category,
                    'organization': {'display_name': 'Test Organization 1', 'key': 'edX'},
                    'marketing_slug': marketing_slug,
                    'status': program_status,
                    'course_codes': course_codes,
                    'subtitle': 'sub',
                    'name': self.program_name
                }]
            }
            parse_data = _get_course_programs(
                self.user, [
                    u'edx/demox/Run_1', u'valid/edX/Course'
                ]
            )

            if program_status == 'unpublished':
                self.assertEqual({}, parse_data)
            else:
                self.assertEqual(
                    {
                        u'edx/demox/Run_1': {
                            'category': self.category,
                            'course_program_list': [{
                                'program_id': 0,
                                'course_count': len(course_codes),
                                'display_name': self.program_name,
                                'program_marketing_url': urljoin(
                                    settings.MKTG_URLS.get('ROOT'), 'xseries' + '/{}'
                                ).format(marketing_slug)
                            }]
                        }
                    },
                    parse_data
                )

    def test_program_courses_on_dashboard_without_configuration(self):
        """If programs configuration is disabled then the xseries upsell messages
        will not appear on student dashboard.
        """
        CourseEnrollment.enroll(self.user, self.course_1.id)
        self.client.login(username="jack", password="test")
        with patch('student.views.get_programs_for_dashboard') as mock_method:
            mock_method.return_value = self._create_program_data([])
            response = self.client.get(reverse('dashboard'))

            self.assertEquals(response.status_code, 200)
            self.assertIn('Pursue a Certificate of Achievement to highlight', response.content)
            self._assert_responses(response, 0)

    @ddt.data('verified', 'honor')
    def test_modes_program_courses_on_dashboard_with_configuration(self, course_mode):
        """Test that if program configuration is enabled than student can only
        see those courses with xseries upsell messages which are active in
        xseries programs.
        """
        CourseEnrollment.enroll(self.user, self.course_1.id, mode=course_mode)
        CourseEnrollment.enroll(self.user, self.course_2.id, mode=course_mode)

        self.client.login(username="jack", password="test")
        self.create_programs_config()

        with patch('student.views.get_programs_for_dashboard') as mock_data:
            mock_data.return_value = self._create_program_data(
                [(self.course_1.id, 'active'), (self.course_2.id, 'unpublished')]
            )
            response = self.client.get(reverse('dashboard'))
            # count total courses appearing on student dashboard
            self.assertContains(response, 'course-container', 2)
            self._assert_responses(response, 1)

            # for verified enrollment view the program detail button will have
            # the class 'base-btn'
            # for other modes view the program detail button will have have the
            # class border-btn
            if course_mode == 'verified':
                self.assertIn('xseries-base-btn', response.content)
            else:
                self.assertIn('xseries-border-btn', response.content)

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    @ddt.data((-2, -1), (-1, 1), (1, 2))
    @ddt.unpack
    def test_start_end_offsets(self, start_days_offset, end_days_offset):
        """Test that the xseries upsell messaging displays whether the course
        has not yet started, is in session, or has already ended.
        """
        self.course_1.start = datetime.now(pytz.UTC) + timedelta(days=start_days_offset)
        self.course_1.end = datetime.now(pytz.UTC) + timedelta(days=end_days_offset)
        self.update_course(self.course_1, self.user.id)
        CourseEnrollment.enroll(self.user, self.course_1.id, mode='verified')

        self.client.login(username="jack", password="test")
        self.create_programs_config()

        with patch(
            'student.views.get_programs_for_dashboard',
            return_value=self._create_program_data([(self.course_1.id, 'active')])
        ) as mock_get_programs:
            response = self.client.get(reverse('dashboard'))
            # ensure that our course id was included in the API call regardless of start/end dates
            __, course_ids = mock_get_programs.call_args[0]
            self.assertEqual(list(course_ids), [self.course_1.id])
            # count total courses appearing on student dashboard
            self._assert_responses(response, 1)

    @ddt.data(
        ('unpublished', 'unpublished', 'unpublished', 0),
        ('active', 'unpublished', 'unpublished', 1),
        ('active', 'active', 'unpublished', 2),
        ('active', 'active', 'active', 3),
    )
    @ddt.unpack
    def test_different_programs_on_dashboard(self, status_1, status_2, status_3, program_count):
        """Test the upsell on student dashboard with different programs
        statuses.
        """

        CourseEnrollment.enroll(self.user, self.course_1.id, mode='verified')
        CourseEnrollment.enroll(self.user, self.course_2.id, mode='honor')
        CourseEnrollment.enroll(self.user, self.course_3.id, mode='honor')

        self.client.login(username="jack", password="test")
        self.create_programs_config()

        with patch('student.views.get_programs_for_dashboard') as mock_data:
            mock_data.return_value = self._create_program_data(
                [(self.course_1.id, status_1),
                 (self.course_2.id, status_2),
                 (self.course_3.id, status_3)]
            )

            response = self.client.get(reverse('dashboard'))
            # count total courses appearing on student dashboard
            self.assertContains(response, 'course-container', 3)
            self._assert_responses(response, program_count)

    @patch('student.views.log.warning')
    @ddt.data('', 'course_codes', 'marketing_slug', 'name')
    def test_program_courses_with_invalid_data(self, key_remove, log_warn):
        """Test programs with invalid responses."""

        CourseEnrollment.enroll(self.user, self.course_1.id)
        self.client.login(username="jack", password="test")
        self.create_programs_config()

        program_data = self._create_program_data([(self.course_1.id, 'active')])
        for program in program_data[unicode(self.course_1.id)]:
            if key_remove and key_remove in program:
                del program[key_remove]

        with patch('student.views.get_programs_for_dashboard') as mock_data:
            mock_data.return_value = program_data

            response = self.client.get(reverse('dashboard'))

            # if data is invalid then warning log will be recorded.
            if key_remove:
                log_warn.assert_called_with(
                    'Program structure is invalid, skipping display: %r', program_data[
                        unicode(self.course_1.id)
                    ][0]
                )
                # verify that no programs related upsell messages appear on the
                # student dashboard.
                self._assert_responses(response, 0)
            else:
                # in case of valid data all upsell messages will appear on dashboard.
                self._assert_responses(response, 1)

            # verify that only normal courses (non-programs courses) appear on
            # the student dashboard.
            self.assertContains(response, 'course-container', 1)
            self.assertIn('Pursue a Certificate of Achievement to highlight', response.content)

    def _assert_responses(self, response, count):
        """Dry method to compare different programs related upsell messages,
        classes.
        """
        self.assertContains(response, 'label-xseries-association', count)
        self.assertContains(response, 'btn xseries-', count)

        self.assertContains(response, '{category} Program Course'.format(category=self.category), count)
        self.assertContains(
            response,
            '{category} Program: Interested in more courses in this subject?'.format(category=self.category),
            count
        )
        self.assertContains(response, 'View {category} Details'.format(category=self.category), count)

        self.assertContains(response, 'This course is 1 of 3 courses in the', count)
        self.assertContains(response, self.program_name, count * 2)


class UserAttributeTests(TestCase):
    """Tests for the UserAttribute model."""

    def setUp(self):
        super(UserAttributeTests, self).setUp()
        self.user = UserFactory()
        self.name = 'test'
        self.value = 'test-value'

    def test_get_set_attribute(self):
        self.assertIsNone(UserAttribute.get_user_attribute(self.user, self.name))
        UserAttribute.set_user_attribute(self.user, self.name, self.value)
        self.assertEqual(UserAttribute.get_user_attribute(self.user, self.name), self.value)
        new_value = 'new_value'
        UserAttribute.set_user_attribute(self.user, self.name, new_value)
        self.assertEqual(UserAttribute.get_user_attribute(self.user, self.name), new_value)

    def test_unicode(self):
        UserAttribute.set_user_attribute(self.user, self.name, self.value)
        for field in (self.name, self.value, self.user.username):
            self.assertIn(field, unicode(UserAttribute.objects.get(user=self.user)))

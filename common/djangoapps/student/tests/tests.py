"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import logging
import unittest
from datetime import datetime, timedelta
import pytz

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.test.client import RequestFactory, Client
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse
from django.contrib.sessions.middleware import SessionMiddleware

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.tests import TEST_DATA_MIXED_MODULESTORE
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from mock import Mock, patch

from student.models import anonymous_id_for_user, user_by_anonymous_id, CourseEnrollment, unique_id_for_user
from student.views import (process_survey_link, _cert_info,
                           change_enrollment, complete_course_mode_info)
from student.tests.factories import UserFactory, CourseModeFactory

from certificates.models import CertificateStatuses
from certificates.tests.factories import GeneratedCertificateFactory
import shoppingcart
from bulk_email.models import Optout

log = logging.getLogger(__name__)


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

    def test_cert_info(self):
        user = Mock(username="fred")
        survey_url = "http://a_survey.com"
        course = Mock(end_of_course_survey_url=survey_url, certificates_display_behavior='end')

        self.assertEqual(
            _cert_info(user, course, None),
            {
                'status': 'processing',
                'show_disabled_download_button': False,
                'show_download_url': False,
                'show_survey_button': False,
            }
        )

        cert_status = {'status': 'unavailable'}
        self.assertEqual(
            _cert_info(user, course, cert_status),
            {
                'status': 'processing',
                'show_disabled_download_button': False,
                'show_download_url': False,
                'show_survey_button': False,
                'mode': None
            }
        )

        cert_status = {'status': 'generating', 'grade': '67', 'mode': 'honor'}
        self.assertEqual(
            _cert_info(user, course, cert_status),
            {
                'status': 'generating',
                'show_disabled_download_button': True,
                'show_download_url': False,
                'show_survey_button': True,
                'survey_url': survey_url,
                'grade': '67',
                'mode': 'honor'
            }
        )

        cert_status = {'status': 'regenerating', 'grade': '67', 'mode': 'verified'}
        self.assertEqual(
            _cert_info(user, course, cert_status),
            {
                'status': 'generating',
                'show_disabled_download_button': True,
                'show_download_url': False,
                'show_survey_button': True,
                'survey_url': survey_url,
                'grade': '67',
                'mode': 'verified'
            }
        )

        download_url = 'http://s3.edx/cert'
        cert_status = {
            'status': 'downloadable', 'grade': '67',
            'download_url': download_url,
            'mode': 'honor'
        }
        self.assertEqual(
            _cert_info(user, course, cert_status),
            {
                'status': 'ready',
                'show_disabled_download_button': False,
                'show_download_url': True,
                'download_url': download_url,
                'show_survey_button': True,
                'survey_url': survey_url,
                'grade': '67',
                'mode': 'honor'
            }
        )

        cert_status = {
            'status': 'notpassing', 'grade': '67',
            'download_url': download_url,
            'mode': 'honor'
        }
        self.assertEqual(
            _cert_info(user, course, cert_status),
            {
                'status': 'notpassing',
                'show_disabled_download_button': False,
                'show_download_url': False,
                'show_survey_button': True,
                'survey_url': survey_url,
                'grade': '67',
                'mode': 'honor'
            }
        )

        # Test a course that doesn't have a survey specified
        course2 = Mock(end_of_course_survey_url=None)
        cert_status = {
            'status': 'notpassing', 'grade': '67',
            'download_url': download_url, 'mode': 'honor'
        }
        self.assertEqual(
            _cert_info(user, course2, cert_status),
            {
                'status': 'notpassing',
                'show_disabled_download_button': False,
                'show_download_url': False,
                'show_survey_button': False,
                'grade': '67',
                'mode': 'honor'
            }
        )

        # test when the display is unavailable or notpassing, we get the correct results out
        course2.certificates_display_behavior = 'early_no_info'
        cert_status = {'status': 'unavailable'}
        self.assertIsNone(_cert_info(user, course2, cert_status))

        cert_status = {
            'status': 'notpassing', 'grade': '67',
            'download_url': download_url,
            'mode': 'honor'
        }
        self.assertIsNone(_cert_info(user, course2, cert_status))


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class DashboardTest(TestCase):
    """
    Tests for dashboard utility functions
    """
    # arbitrary constant
    COURSE_SLUG = "100"
    COURSE_NAME = "test_course"
    COURSE_ORG = "EDX"

    def setUp(self):
        self.course = CourseFactory.create(org=self.COURSE_ORG, display_name=self.COURSE_NAME, number=self.COURSE_SLUG)
        self.assertIsNotNone(self.course)
        self.user = UserFactory.create(username="jack", email="jack@fake.edx.org", password='test')
        self.client = Client()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def check_verification_status_on(self, mode, value):
        """
        Check that the css class and the status message are in the dashboard html.
        """
        CourseEnrollment.enroll(self.user, self.course.location.course_key, mode=mode)
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, "class=\"course {0}\"".format(mode))
        self.assertContains(response, value)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_VERIFIED_CERTIFICATES': True})
    def test_verification_status_visible(self):
        """
        Test that the certificate verification status for courses is visible on the dashboard.
        """
        self.client.login(username="jack", password="test")
        self.check_verification_status_on('verified', 'You\'re enrolled as a verified student')
        self.check_verification_status_on('honor', 'You\'re enrolled as an honor code student')
        self.check_verification_status_on('audit', 'You\'re auditing this course')

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def check_verification_status_off(self, mode, value):
        """
        Check that the css class and the status message are not in the dashboard html.
        """
        CourseEnrollment.enroll(self.user, self.course.location.course_key, mode=mode)
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, "class=\"course {0}\"".format(mode))
        self.assertNotContains(response, value)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_VERIFIED_CERTIFICATES': False})
    def test_verification_status_invisible(self):
        """
        Test that the certificate verification status for courses is not visible on the dashboard
        if the verified certificates setting is off.
        """
        self.client.login(username="jack", password="test")
        self.check_verification_status_off('verified', 'You\'re enrolled as a verified student')
        self.check_verification_status_off('honor', 'You\'re enrolled as an honor code student')
        self.check_verification_status_off('audit', 'You\'re auditing this course')

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
    def test_refundable(self):
        verified_mode = CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='verified',
            mode_display_name='Verified',
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=1)
        )
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode='verified')

        self.assertTrue(enrollment.refundable())

        verified_mode.expiration_datetime = datetime.now(pytz.UTC) - timedelta(days=1)
        verified_mode.save()
        self.assertFalse(enrollment.refundable())

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @patch('courseware.views.log.warning')
    def test_blocked_course_scenario(self, log_warning):

        self.client.login(username="jack", password="test")

        #create testing invoice 1
        sale_invoice_1 = shoppingcart.models.Invoice.objects.create(
            total_amount=1234.32, company_name='Test1', company_contact_name='Testw',
            company_contact_email='test1@test.com', customer_reference_number='2Fwe23S',
            recipient_name='Testw_1', recipient_email='test2@test.com', internal_reference="A",
            course_id=self.course.id, is_valid=False
        )
        course_reg_code = shoppingcart.models.CourseRegistrationCode(code="abcde", course_id=self.course.id,
                                                                     created_by=self.user, invoice=sale_invoice_1)
        course_reg_code.save()

        cart = shoppingcart.models.Order.get_cart_for_user(self.user)
        shoppingcart.models.PaidCourseRegistration.add_to_order(cart, self.course.id)
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': course_reg_code.code})
        self.assertEqual(resp.status_code, 200)

        # freely enroll the user into course
        resp = self.client.get(reverse('shoppingcart.views.register_courses'))
        self.assertIn('success', resp.content)

        response = self.client.get(reverse('dashboard'))
        self.assertIn('You can no longer access this course because payment has not yet been received', response.content)
        optout_object = Optout.objects.filter(user=self.user, course_id=self.course.id)
        self.assertEqual(len(optout_object), 1)

        # Direct link to course redirect to user dashboard
        self.client.get(reverse('courseware', kwargs={"course_id": self.course.id.to_deprecated_string()}))
        log_warning.assert_called_with(
            u'User %s cannot access the course %s because payment has not yet been received', self.user, self.course.id.to_deprecated_string())

        # Now re-validating the invoice
        invoice = shoppingcart.models.Invoice.objects.get(id=sale_invoice_1.id)
        invoice.is_valid = True
        invoice.save()

        response = self.client.get(reverse('dashboard'))
        self.assertNotIn('You can no longer access this course because payment has not yet been received', response.content)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_refundable_of_purchased_course(self):

        self.client.login(username="jack", password="test")
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            min_price=10,
            currency='usd',
            mode_display_name='honor',
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=1)
        )
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode='honor')

        # TODO: Until we can allow course administrators to define a refund period for paid for courses show_refund_option should be False. # pylint: disable=W0511
        self.assertFalse(enrollment.refundable())

        resp = self.client.post(reverse('student.views.dashboard', args=[]))
        self.assertIn('You will not be refunded the amount you paid.', resp.content)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_refundable_when_certificate_exists(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='verified',
            mode_display_name='Verified',
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=1)
        )
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode='verified')

        self.assertTrue(enrollment.refundable())

        GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified'
        )

        self.assertFalse(enrollment.refundable())


class EnrollInCourseTest(TestCase):
    """Tests enrolling and unenrolling in courses."""

    def setUp(self):
        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

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

    def assert_no_events_were_emitted(self):
        """Ensures no events were emitted since the last event related assertion"""
        self.assertFalse(self.mock_tracker.emit.called)  # pylint: disable=maybe-no-member
        self.mock_tracker.reset_mock()

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
                'mode': 'honor'
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
                'mode': 'honor'
            }
        )
        self.mock_tracker.reset_mock()

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

        CourseEnrollment.enroll(user, course_id)
        self.assert_enrollment_event_was_emitted(user, course_id)

        CourseEnrollment.enroll(user, course_id, "audit")
        self.assert_enrollment_mode_change_event_was_emitted(user, course_id, "audit")

        # same enrollment mode does not emit an event
        CourseEnrollment.enroll(user, course_id, "audit")
        self.assert_no_events_were_emitted()

        CourseEnrollment.enroll(user, course_id, "honor")
        self.assert_enrollment_mode_change_event_was_emitted(user, course_id, "honor")


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
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

    def test_enroll_as_honor(self):
        """Tests that a student can successfully enroll through this view"""
        response = self._enroll_through_view(self.course)
        self.assertEqual(response.status_code, 200)
        enrollment_mode, is_active = CourseEnrollment.enrollment_mode_for_user(
            self.user, self.course.id
        )
        self.assertTrue(is_active)
        self.assertEqual(enrollment_mode, u'honor')

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

    def test_change_to_honor_if_verified(self):
        """
        Tests that a student that is a currently enrolled verified student cannot
        accidentally change their enrollment to verified
        """
        CourseEnrollment.enroll(self.user, self.course.id, mode=u'verified')
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        # now try to enroll the student in the honor mode:
        response = self._enroll_through_view(self.course)
        self.assertEqual(response.status_code, 400)
        enrollment_mode, is_active = CourseEnrollment.enrollment_mode_for_user(
            self.user, self.course.id
        )
        self.assertTrue(is_active)
        self.assertEqual(enrollment_mode, u'verified')

    def test_change_to_honor_if_verified_not_active(self):
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
        self.assertEqual(enrollment_mode, u'honor')


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class PaidRegistrationTest(ModuleStoreTestCase):
    """
    Tests for paid registration functionality (not verified student), involves shoppingcart
    """
    # arbitrary constant
    COURSE_SLUG = "100"
    COURSE_NAME = "test_course"
    COURSE_ORG = "EDX"

    def setUp(self):
        # Create course
        self.req_factory = RequestFactory()
        self.course = CourseFactory.create(org=self.COURSE_ORG, display_name=self.COURSE_NAME, number=self.COURSE_SLUG)
        self.assertIsNotNone(self.course)
        self.user = User.objects.create(username="jack", email="jack@fake.edx.org")

    @unittest.skipUnless(settings.FEATURES.get('ENABLE_SHOPPING_CART'), "Shopping Cart not enabled in settings")
    def test_change_enrollment_add_to_cart(self):
        request = self.req_factory.post(
            reverse('change_enrollment'), {
                'course_id': self.course.id.to_deprecated_string(),
                'enrollment_action': 'add_to_cart'
            }
        )

        # Add a session to the request
        SessionMiddleware().process_request(request)
        request.session.save()

        request.user = self.user
        response = change_enrollment(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, reverse('shoppingcart.views.show_cart'))
        self.assertTrue(shoppingcart.models.PaidCourseRegistration.contained_in_order(
            shoppingcart.models.Order.get_cart_for_user(self.user), self.course.id))


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AnonymousLookupTable(TestCase):
    """
    Tests for anonymous_id_functions
    """
    # arbitrary constant
    COURSE_SLUG = "100"
    COURSE_NAME = "test_course"
    COURSE_ORG = "EDX"

    def setUp(self):
        self.course = CourseFactory.create(org=self.COURSE_ORG, display_name=self.COURSE_NAME, number=self.COURSE_SLUG)
        self.assertIsNotNone(self.course)
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

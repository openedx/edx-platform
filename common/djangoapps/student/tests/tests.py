"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import logging
import json
import re
import unittest
from datetime import datetime, timedelta
import pytz

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from django.contrib.auth.hashers import UNUSABLE_PASSWORD
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import int_to_base36
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.tests import TEST_DATA_MIXED_MODULESTORE

from mock import Mock, patch, sentinel
from textwrap import dedent

from student.models import unique_id_for_user, CourseEnrollment
from student.views import (process_survey_link, _cert_info, password_reset, password_reset_confirm_wrapper,
                           change_enrollment, complete_course_mode_info)
from student.tests.factories import UserFactory, CourseModeFactory
from student.tests.test_email import mock_render_to_string

import shoppingcart

COURSE_1 = 'edX/toy/2012_Fall'
COURSE_2 = 'edx/full/6.002_Spring_2012'

log = logging.getLogger(__name__)


class ResetPasswordTests(TestCase):
    """ Tests that clicking reset password sends email, and doesn't activate the user
    """
    request_factory = RequestFactory()

    def setUp(self):
        self.user = UserFactory.create()
        self.user.is_active = False
        self.user.save()
        self.token = default_token_generator.make_token(self.user)
        self.uidb36 = int_to_base36(self.user.id)

        self.user_bad_passwd = UserFactory.create()
        self.user_bad_passwd.is_active = False
        self.user_bad_passwd.password = UNUSABLE_PASSWORD
        self.user_bad_passwd.save()

    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_user_bad_password_reset(self):
        """Tests password reset behavior for user with password marked UNUSABLE_PASSWORD"""

        bad_pwd_req = self.request_factory.post('/password_reset/', {'email': self.user_bad_passwd.email})
        bad_pwd_resp = password_reset(bad_pwd_req)
        # If they've got an unusable password, we return a successful response code
        self.assertEquals(bad_pwd_resp.status_code, 200)
        self.assertEquals(bad_pwd_resp.content, json.dumps({'success': True,
                                                            'value': "('registration/password_reset_done.html', [])"}))

    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_nonexist_email_password_reset(self):
        """Now test the exception cases with of reset_password called with invalid email."""

        bad_email_req = self.request_factory.post('/password_reset/', {'email': self.user.email+"makeItFail"})
        bad_email_resp = password_reset(bad_email_req)
        # Note: even if the email is bad, we return a successful response code
        # This prevents someone potentially trying to "brute-force" find out which emails are and aren't registered with edX
        self.assertEquals(bad_email_resp.status_code, 200)
        self.assertEquals(bad_email_resp.content, json.dumps({'success': True,
                                                              'value': "('registration/password_reset_done.html', [])"}))

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_PASSWORD_RESET_EMAIL_TEST', False),
                         dedent("""Skipping Test because CMS has not provided necessary templates for password reset.
                                If LMS tests print this message, that needs to be fixed."""))
    @patch('django.core.mail.send_mail')
    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_reset_password_email(self, send_email):
        """Tests contents of reset password email, and that user is not active"""

        good_req = self.request_factory.post('/password_reset/', {'email': self.user.email})
        good_resp = password_reset(good_req)
        self.assertEquals(good_resp.status_code, 200)
        self.assertEquals(good_resp.content,
                          json.dumps({'success': True,
                                      'value': "('registration/password_reset_done.html', [])"}))

        ((subject, msg, from_addr, to_addrs), sm_kwargs) = send_email.call_args
        self.assertIn("Password reset", subject)
        self.assertIn("You're receiving this e-mail because you requested a password reset", msg)
        self.assertEquals(from_addr, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(len(to_addrs), 1)
        self.assertIn(self.user.email, to_addrs)

        #test that the user is not active
        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)
        reset_match = re.search(r'password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/', msg).groupdict()

    @patch('student.views.password_reset_confirm')
    def test_reset_password_bad_token(self, reset_confirm):
        """Tests bad token and uidb36 in password reset"""

        bad_reset_req = self.request_factory.get('/password_reset_confirm/NO-OP/')
        password_reset_confirm_wrapper(bad_reset_req, 'NO', 'OP')
        (confirm_args, confirm_kwargs) = reset_confirm.call_args
        self.assertEquals(confirm_kwargs['uidb36'], 'NO')
        self.assertEquals(confirm_kwargs['token'], 'OP')
        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)

    @patch('student.views.password_reset_confirm')
    def test_reset_password_good_token(self, reset_confirm):
        """Tests good token and uidb36 in password reset"""

        good_reset_req = self.request_factory.get('/password_reset_confirm/{0}-{1}/'.format(self.uidb36, self.token))
        password_reset_confirm_wrapper(good_reset_req, self.uidb36, self.token)
        (confirm_args, confirm_kwargs) = reset_confirm.call_args
        self.assertEquals(confirm_kwargs['uidb36'], self.uidb36)
        self.assertEquals(confirm_kwargs['token'], self.token)
        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.is_active)


class CourseEndingTest(TestCase):
    """Test things related to course endings: certificates, surveys, etc"""

    def test_process_survey_link(self):
        username = "fred"
        user = Mock(username=username)
        id = unique_id_for_user(user)
        link1 = "http://www.mysurvey.com"
        self.assertEqual(process_survey_link(link1, user), link1)

        link2 = "http://www.mysurvey.com?unique={UNIQUE_ID}"
        link2_expected = "http://www.mysurvey.com?unique={UNIQUE_ID}".format(UNIQUE_ID=id)
        self.assertEqual(process_survey_link(link2, user), link2_expected)

    def test_cert_info(self):
        user = Mock(username="fred")
        survey_url = "http://a_survey.com"
        course = Mock(end_of_course_survey_url=survey_url)

        self.assertEqual(_cert_info(user, course, None),
                         {'status': 'processing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': False,
                          })

        cert_status = {'status': 'unavailable'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'processing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': False,
                          'mode': None
                          })

        cert_status = {'status': 'generating', 'grade': '67', 'mode': 'honor'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'generating',
                          'show_disabled_download_button': True,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67',
                          'mode': 'honor'
                          })

        cert_status = {'status': 'regenerating', 'grade': '67', 'mode': 'verified'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'generating',
                          'show_disabled_download_button': True,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67',
                          'mode': 'verified'
                          })

        download_url = 'http://s3.edx/cert'
        cert_status = {'status': 'downloadable', 'grade': '67',
                       'download_url': download_url, 'mode': 'honor'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'ready',
                          'show_disabled_download_button': False,
                          'show_download_url': True,
                          'download_url': download_url,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67',
                          'mode': 'honor'
                          })

        cert_status = {'status': 'notpassing', 'grade': '67',
                       'download_url': download_url, 'mode': 'honor'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'notpassing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67',
                          'mode': 'honor'
                          })

        # Test a course that doesn't have a survey specified
        course2 = Mock(end_of_course_survey_url=None)
        cert_status = {'status': 'notpassing', 'grade': '67',
                       'download_url': download_url, 'mode': 'honor'}
        self.assertEqual(_cert_info(user, course2, cert_status),
                         {'status': 'notpassing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': False,
                          'grade': '67',
                          'mode': 'honor'
                          })


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
        self.user = UserFactory.create(username="jack", email="jack@fake.edx.org")
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor Code',
        )

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



class EnrollInCourseTest(TestCase):
    """Tests enrolling and unenrolling in courses."""

    def setUp(self):
        patcher = patch('student.models.server_track')
        self.mock_server_track = patcher.start()
        self.addCleanup(patcher.stop)

        crum_patcher = patch('student.models.crum.get_current_request')
        self.mock_get_current_request = crum_patcher.start()
        self.addCleanup(crum_patcher.stop)
        self.mock_get_current_request.return_value = sentinel.request

    def test_enrollment(self):
        user = User.objects.create_user("joe", "joe@joe.com", "password")
        course_id = "edX/Test101/2013"
        course_id_partial = "edX/Test101"

        # Test basic enrollment
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assertFalse(CourseEnrollment.is_enrolled_by_partial(user,
            course_id_partial))
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assertTrue(CourseEnrollment.is_enrolled_by_partial(user,
            course_id_partial))
        self.assert_enrollment_event_was_emitted(user, course_id)

        # Enrolling them again should be harmless
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assertTrue(CourseEnrollment.is_enrolled_by_partial(user,
            course_id_partial))
        self.assert_no_events_were_emitted()

        # Now unenroll the user
        CourseEnrollment.unenroll(user, course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assertFalse(CourseEnrollment.is_enrolled_by_partial(user,
            course_id_partial))
        self.assert_unenrollment_event_was_emitted(user, course_id)

        # Unenrolling them again should also be harmless
        CourseEnrollment.unenroll(user, course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assertFalse(CourseEnrollment.is_enrolled_by_partial(user,
            course_id_partial))
        self.assert_no_events_were_emitted()

        # The enrollment record should still exist, just be inactive
        enrollment_record = CourseEnrollment.objects.get(
            user=user,
            course_id=course_id
        )
        self.assertFalse(enrollment_record.is_active)

    def assert_no_events_were_emitted(self):
        """Ensures no events were emitted since the last event related assertion"""
        self.assertFalse(self.mock_server_track.called)
        self.mock_server_track.reset_mock()

    def assert_enrollment_event_was_emitted(self, user, course_id):
        """Ensures an enrollment event was emitted since the last event related assertion"""
        self.mock_server_track.assert_called_once_with(
            sentinel.request,
            'edx.course.enrollment.activated',
            {
                'course_id': course_id,
                'user_id': user.pk,
                'mode': 'honor'
            }
        )
        self.mock_server_track.reset_mock()

    def assert_unenrollment_event_was_emitted(self, user, course_id):
        """Ensures an unenrollment event was emitted since the last event related assertion"""
        self.mock_server_track.assert_called_once_with(
            sentinel.request,
            'edx.course.enrollment.deactivated',
            {
                'course_id': course_id,
                'user_id': user.pk,
                'mode': 'honor'
            }
        )
        self.mock_server_track.reset_mock()

    def test_enrollment_non_existent_user(self):
        # Testing enrollment of newly unsaved user (i.e. no database entry)
        user = User(username="rusty", email="rusty@fake.edx.org")
        course_id = "edX/Test101/2013"

        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Unenroll does nothing
        CourseEnrollment.unenroll(user, course_id)
        self.assert_no_events_were_emitted()

        # Implicit save() happens on new User object when enrolling, so this
        # should still work
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_enrollment_event_was_emitted(user, course_id)

    def test_enrollment_by_email(self):
        user = User.objects.create(username="jack", email="jack@fake.edx.org")
        course_id = "edX/Test101/2013"

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

    def test_enrollment_multiple_classes(self):
        user = User(username="rusty", email="rusty@fake.edx.org")
        course_id1 = "edX/Test101/2013"
        course_id2 = "MITx/6.003z/2012"

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

    def test_activation(self):
        user = User.objects.create(username="jack", email="jack@fake.edx.org")
        course_id = "edX/Test101/2013"
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

    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SHOPPING_CART'), "Shopping Cart not enabled in settings")
    def test_change_enrollment_add_to_cart(self):
        request = self.req_factory.post(reverse('change_enrollment'), {'course_id': self.course.id,
                                                                       'enrollment_action': 'add_to_cart'})
        request.user = self.user
        response = change_enrollment(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, reverse('shoppingcart.views.show_cart'))
        self.assertTrue(shoppingcart.models.PaidCourseRegistration.contained_in_order(
            shoppingcart.models.Order.get_cart_for_user(self.user), self.course.id))

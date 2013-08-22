"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import logging
import json
import re
import unittest

from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from django.contrib.auth.hashers import UNUSABLE_PASSWORD
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import int_to_base36


from mock import Mock, patch
from textwrap import dedent

from student.models import unique_id_for_user, CourseEnrollment
from student.views import process_survey_link, _cert_info, password_reset, password_reset_confirm_wrapper
from student.tests.factories import UserFactory
from student.tests.test_email import mock_render_to_string
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

    def test_user_bad_password_reset(self):
        """Tests password reset behavior for user with password marked UNUSABLE_PASSWORD"""

        bad_pwd_req = self.request_factory.post('/password_reset/', {'email': self.user_bad_passwd.email})
        bad_pwd_resp = password_reset(bad_pwd_req)
        self.assertEquals(bad_pwd_resp.status_code, 200)
        self.assertEquals(bad_pwd_resp.content, json.dumps({'success': False,
                                                            'error': 'Invalid e-mail or user'}))

    def test_nonexist_email_password_reset(self):
        """Now test the exception cases with of reset_password called with invalid email."""

        bad_email_req = self.request_factory.post('/password_reset/', {'email': self.user.email+"makeItFail"})
        bad_email_resp = password_reset(bad_email_req)
        self.assertEquals(bad_email_resp.status_code, 200)
        self.assertEquals(bad_email_resp.content, json.dumps({'success': False,
                                                              'error': 'Invalid e-mail or user'}))

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
                          'show_survey_button': False, })

        cert_status = {'status': 'unavailable'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'processing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': False})

        cert_status = {'status': 'generating', 'grade': '67'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'generating',
                          'show_disabled_download_button': True,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67'
                          })

        cert_status = {'status': 'regenerating', 'grade': '67'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'generating',
                          'show_disabled_download_button': True,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67'
                          })

        download_url = 'http://s3.edx/cert'
        cert_status = {'status': 'downloadable', 'grade': '67',
                       'download_url': download_url}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'ready',
                          'show_disabled_download_button': False,
                          'show_download_url': True,
                          'download_url': download_url,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67'
                          })

        cert_status = {'status': 'notpassing', 'grade': '67',
                       'download_url': download_url}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'notpassing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67'
                          })

        # Test a course that doesn't have a survey specified
        course2 = Mock(end_of_course_survey_url=None)
        cert_status = {'status': 'notpassing', 'grade': '67',
                       'download_url': download_url}
        self.assertEqual(_cert_info(user, course2, cert_status),
                         {'status': 'notpassing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': False,
                          'grade': '67'
                          })


class EnrollInCourseTest(TestCase):
    """Tests enrolling and unenrolling in courses."""

    def test_enrollment(self):
        user = User.objects.create_user("joe", "joe@joe.com", "password")
        course_id = "edX/Test101/2013"

        # Test basic enrollment
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))

        # Enrolling them again should be harmless
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))

        # Now unenroll the user
        CourseEnrollment.unenroll(user, course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Unenrolling them again should also be harmless
        CourseEnrollment.unenroll(user, course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # The enrollment record should still exist, just be inactive
        enrollment_record = CourseEnrollment.objects.get(
            user=user,
            course_id=course_id
        )
        self.assertFalse(enrollment_record.is_active)

    def test_enrollment_non_existent_user(self):
        # Testing enrollment of newly unsaved user (i.e. no database entry)
        user = User(username="rusty", email="rusty@fake.edx.org")
        course_id = "edX/Test101/2013"

        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Unenroll does nothing
        CourseEnrollment.unenroll(user, course_id)

        # Implicit save() happens on new User object when enrolling, so this
        # should still work
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))

    def test_enrollment_by_email(self):
        user = User.objects.create(username="jack", email="jack@fake.edx.org")
        course_id = "edX/Test101/2013"

        CourseEnrollment.enroll_by_email("jack@fake.edx.org", course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))

        # This won't throw an exception, even though the user is not found
        self.assertIsNone(
            CourseEnrollment.enroll_by_email("not_jack@fake.edx.org", course_id)
        )

        self.assertRaises(
            User.DoesNotExist,
            CourseEnrollment.enroll_by_email,
            "not_jack@fake.edx.org",
            course_id,
            ignore_errors=False
        )

        # Now unenroll them by email
        CourseEnrollment.unenroll_by_email("jack@fake.edx.org", course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Harmless second unenroll
        CourseEnrollment.unenroll_by_email("jack@fake.edx.org", course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Unenroll on non-existent user shouldn't throw an error
        CourseEnrollment.unenroll_by_email("not_jack@fake.edx.org", course_id)

    def test_enrollment_multiple_classes(self):
        user = User(username="rusty", email="rusty@fake.edx.org")
        course_id1 = "edX/Test101/2013"
        course_id2 = "MITx/6.003z/2012"

        CourseEnrollment.enroll(user, course_id1)
        CourseEnrollment.enroll(user, course_id2)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id1))
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id2))

        CourseEnrollment.unenroll(user, course_id1)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id1))
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id2))

        CourseEnrollment.unenroll(user, course_id2)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id1))
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id2))

    def test_activation(self):
        user = User.objects.create(username="jack", email="jack@fake.edx.org")
        course_id = "edX/Test101/2013"
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Creating an enrollment doesn't actually enroll a student
        # (calling CourseEnrollment.enroll() would have)
        enrollment = CourseEnrollment.create_enrollment(user, course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Until you explicitly activate it
        enrollment.activate()
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))

        # Activating something that's already active does nothing
        enrollment.activate()
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))

        # Now deactive
        enrollment.deactivate()
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Deactivating something that's already inactive does nothing
        enrollment.deactivate()
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # A deactivated enrollment should be activated if enroll() is called
        # for that user/course_id combination
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))

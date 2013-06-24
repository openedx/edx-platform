"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import logging
import json
import re
import unittest

from django import forms
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from django.contrib.auth.hashers import UNUSABLE_PASSWORD
from django.template.loader import render_to_string, get_template, TemplateDoesNotExist
from django.core.urlresolvers import is_valid_path

from mock import Mock, patch
from textwrap import dedent

from student.models import unique_id_for_user
from student.views import process_survey_link, _cert_info, password_reset, password_reset_confirm_wrapper
from student.tests.factories import UserFactory
from student.tests.test_email import mock_render_to_string
COURSE_1 = 'edX/toy/2012_Fall'
COURSE_2 = 'edx/full/6.002_Spring_2012'

log = logging.getLogger(__name__)

try:
    get_template('registration/password_reset_email.html')
    project_uses_password_reset = True
except TemplateDoesNotExist:
    project_uses_password_reset = False


class ResetPasswordTests(TestCase):
    """ Tests that clicking reset password sends email, and doesn't activate the user
    """
    request_factory = RequestFactory()

    def setUp(self):
        self.user = UserFactory.create()
        self.user.is_active = False
        self.user.save()

        self.user_bad_passwd = UserFactory.create()
        self.user_bad_passwd.is_active = False
        self.user_bad_passwd.password = UNUSABLE_PASSWORD
        self.user_bad_passwd.save()


    @unittest.skipUnless(project_uses_password_reset, dedent("""Skipping Test because CMS has not provided
    necessary templates for password reset.  If this message is in LMS tests, that is a bug and needs to be fixed."""))
    @patch('student.views.password_reset_confirm')
    @patch('django.core.mail.send_mail')
    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_reset_password_email(self, send_email, reset_confirm):
        """Tests sending of reset password email"""

        #First test the bad password user, mainly for diff-cover sake
        bad_pwd_req = self.request_factory.post('/password_reset/', {'email': self.user_bad_passwd.email})
        bad_pwd_resp = password_reset(bad_pwd_req)
        self.assertEquals(bad_pwd_resp.status_code, 200)
        self.assertEquals(bad_pwd_resp.content, json.dumps({'success': False,
                                                            'error': 'Invalid e-mail or user'}))

        #Now test the exception cases with invalid email.
        bad_email_req = self.request_factory.post('/password_reset/', {'email': self.user.email+"makeItFail"})
        bad_email_resp = password_reset(bad_email_req)
        self.assertEquals(bad_email_resp.status_code, 200)
        self.assertEquals(bad_email_resp.content, json.dumps({'success': False,
                                                              'error': 'Invalid e-mail or user'}))

        #Now test the legit case where email should have been sent
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
        #it's a bit unsettling that we have to reload the user from the db for this test to work
        #but I guess the user is cached here in the instance of ResetPasswordTests
        #so the update in the view does not know to update this class.
        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)

        #now try to activate the user in the password reset phase
        bad_reset_req = self.request_factory.get('/password_reset_confirm/NO-OP/')
        bad_reset_resp = password_reset_confirm_wrapper(bad_reset_req, 'NO', 'OP')
        (confirm_args, confirm_kwargs) = reset_confirm.call_args
        self.assertEquals(confirm_kwargs['uidb36'], 'NO')
        self.assertEquals(confirm_kwargs['token'], 'OP')
        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)

        reset_match = re.search(r'password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/', msg).groupdict()
        good_reset_req = self.request_factory.get('/password_reset_confirm/{0}-{1}/'.format(reset_match['uidb36'],
                                                                                            reset_match['token']))
        good_reset_resp = password_reset_confirm_wrapper(good_reset_req, reset_match['uidb36'], reset_match['token'])
        (confirm_args, confirm_kwargs) = reset_confirm.call_args
        self.assertEquals(confirm_kwargs['uidb36'], reset_match['uidb36'])
        self.assertEquals(confirm_kwargs['token'], reset_match['token'])
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

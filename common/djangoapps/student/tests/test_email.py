
import json
import django.db
import unittest

from student.tests.factories import UserFactory, RegistrationFactory, PendingEmailChangeFactory
from student.views import notify_enrollment_by_email
from student.views import (
    reactivation_email_for_user, do_email_change_request, confirm_email_change,
    validate_new_email, SETTING_CHANGE_INITIATED
)
from student.models import UserProfile, PendingEmailChange
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.auth.models import User
from django.db import transaction
from django.test import TestCase, TransactionTestCase
from django.test.client import RequestFactory
from mock import Mock, patch
from django.http import HttpResponse
from django.conf import settings
from edxmako.shortcuts import render_to_string
from edxmako.tests import mako_middleware_process_request
from util.request import safe_get_host
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from util.testing import EventTestMixin
from openedx.core.djangoapps.theming.test_util import with_is_edx_domain


class TestException(Exception):
    """Exception used for testing that nothing will catch explicitly"""
    pass


def mock_render_to_string(template_name, context):
    """Return a string that encodes template_name and context"""
    return str((template_name, sorted(context.iteritems())))


def mock_render_to_response(template_name, context):
    """Return an HttpResponse with content that encodes template_name and context"""
    # This simulates any db access in the templates.
    UserProfile.objects.exists()
    return HttpResponse(mock_render_to_string(template_name, context))


class EmailTestMixin(object):
    """Adds useful assertions for testing `email_user`"""

    def assertEmailUser(self, email_user, subject_template, subject_context, body_template, body_context):
        """Assert that `email_user` was used to send and email with the supplied subject and body

        `email_user`: The mock `django.contrib.auth.models.User.email_user` function
            to verify
        `subject_template`: The template to have been used for the subject
        `subject_context`: The context to have been used for the subject
        `body_template`: The template to have been used for the body
        `body_context`: The context to have been used for the body
        """
        email_user.assert_called_with(
            mock_render_to_string(subject_template, subject_context),
            mock_render_to_string(body_template, body_context),
            settings.DEFAULT_FROM_EMAIL
        )

    def append_allowed_hosts(self, hostname):
        """ Append hostname to settings.ALLOWED_HOSTS """
        settings.ALLOWED_HOSTS.append(hostname)
        self.addCleanup(settings.ALLOWED_HOSTS.pop)


class EnrollmentEmailTests(ModuleStoreTestCase):
    """ Test senging automated emails to users upon course enrollment. """
    def setUp(self):
        # Test Contstants
        super(EnrollmentEmailTests, self).setUp()
        COURSE_SLUG = "100"
        COURSE_NAME = "test_course"
        COURSE_ORG = "EDX"

        self.user = UserFactory(username="tester", email="tester@gmail.com", password="test")
        self.course = CourseFactory(org=COURSE_ORG, display_name=COURSE_NAME, number=COURSE_SLUG)
        self.assertIsNotNone(self.course)
        self.request = RequestFactory().post('random_url')
        self.request.user = self.user

    def send_enrollment_email(self):
        """ Send enrollment email to the user and return the Json response data. """
        return json.loads(notify_enrollment_by_email(self.course, self.user, self.request).content)

    def test_disabled_email_case(self):
        """ Make sure emails don't fire when enable_enrollment_email setting is disabled. """
        self.course.enable_enrollment_email = False
        email_result = self.send_enrollment_email()
        self.assertIn('email_did_fire', email_result)
        self.assertFalse(email_result['email_did_fire'])

    def test_custom_enrollment_email_sent(self):
        """ Test sending of enrollment emails when enable_default_enrollment_email setting is disabled. """
        self.course.enable_enrollment_email = True
        email_result = self.send_enrollment_email()
        self.assertNotIn('email_did_fire', email_result)
        self.assertIn('is_success', email_result)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ActivationEmailTests(TestCase):
    """Test sending of the activation email. """

    ACTIVATION_SUBJECT = "Activate Your {platform} Account".format(platform=settings.PLATFORM_NAME)

    # Text fragments we expect in the body of an email
    # sent from an OpenEdX installation.
    OPENEDX_FRAGMENTS = [
        "Thank you for signing up for {platform}.".format(platform=settings.PLATFORM_NAME),
        "http://edx.org/activate/",
        "For more information, check our Help Center here: ",
    ]

    # Text fragments we expect in the body of an email
    # sent from an EdX-controlled domain.
    EDX_DOMAIN_FRAGMENTS = [
        "Thank you for signing up for {platform}".format(platform=settings.PLATFORM_NAME),
        "http://edx.org/activate/",
        "https://www.edx.org/contact-us",
        "This email was automatically sent by edx.org"
    ]

    def setUp(self):
        super(ActivationEmailTests, self).setUp()

    def test_activation_email(self):
        self._create_account()
        self._assert_activation_email(self.ACTIVATION_SUBJECT, self.OPENEDX_FRAGMENTS)

    @with_is_edx_domain(True)
    def test_activation_email_edx_domain(self):
        self._create_account()
        self._assert_activation_email(self.ACTIVATION_SUBJECT, self.EDX_DOMAIN_FRAGMENTS)

    def _create_account(self):
        """Create an account, triggering the activation email. """
        url = reverse('create_account')
        params = {
            'username': 'test_user',
            'email': 'test_user@example.com',
            'password': 'edx',
            'name': 'Test User',
            'honor_code': True,
            'terms_of_service': True
        }
        resp = self.client.post(url, params)
        self.assertEqual(
            resp.status_code, 200,
            msg=u"Could not create account (status {status}). The response was {response}".format(
                status=resp.status_code,
                response=resp.content
            )
        )

    def _assert_activation_email(self, subject, body_fragments):
        """Verify that the activation email was sent. """
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, subject)
        for fragment in body_fragments:
            self.assertIn(fragment, msg.body)


@patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
@patch('django.contrib.auth.models.User.email_user')
class ReactivationEmailTests(EmailTestMixin, TestCase):
    """Test sending a reactivation email to a user"""

    def setUp(self):
        super(ReactivationEmailTests, self).setUp()
        self.user = UserFactory.create()
        self.unregisteredUser = UserFactory.create()
        self.registration = RegistrationFactory.create(user=self.user)

    def reactivation_email(self, user):
        """
        Send the reactivation email to the specified user,
        and return the response as json data.
        """
        return json.loads(reactivation_email_for_user(user).content)

    def assertReactivateEmailSent(self, email_user):
        """Assert that the correct reactivation email has been sent"""
        context = {
            'name': self.user.profile.name,
            'key': self.registration.activation_key
        }

        self.assertEmailUser(
            email_user,
            'emails/activation_email_subject.txt',
            context,
            'emails/activation_email.txt',
            context
        )

        # Thorough tests for safe_get_host are elsewhere; here we just want a quick URL sanity check
        request = RequestFactory().post('unused_url')
        request.user = self.user
        request.META['HTTP_HOST'] = "aGenericValidHostName"
        self.append_allowed_hosts("aGenericValidHostName")

        mako_middleware_process_request(request)
        body = render_to_string('emails/activation_email.txt', context)
        host = safe_get_host(request)

        self.assertIn(host, body)

    def test_reactivation_email_failure(self, email_user):
        self.user.email_user.side_effect = Exception
        response_data = self.reactivation_email(self.user)

        self.assertReactivateEmailSent(email_user)
        self.assertFalse(response_data['success'])

    def test_reactivation_for_unregistered_user(self, email_user):
        """
        Test that trying to send a reactivation email to an unregistered
        user fails without throwing a 500 error.
        """
        response_data = self.reactivation_email(self.unregisteredUser)

        self.assertFalse(response_data['success'])

    def test_reactivation_email_success(self, email_user):
        response_data = self.reactivation_email(self.user)

        self.assertReactivateEmailSent(email_user)
        self.assertTrue(response_data['success'])


class EmailChangeRequestTests(EventTestMixin, TestCase):
    """Test changing a user's email address"""

    def setUp(self):
        super(EmailChangeRequestTests, self).setUp('student.views.tracker')
        self.user = UserFactory.create()
        self.new_email = 'new.email@edx.org'
        self.req_factory = RequestFactory()
        self.request = self.req_factory.post('unused_url', data={
            'password': 'test',
            'new_email': self.new_email
        })
        self.request.user = self.user
        self.user.email_user = Mock()

    def do_email_validation(self, email):
        """Executes validate_new_email, returning any resulting error message. """
        try:
            validate_new_email(self.request.user, email)
        except ValueError as err:
            return err.message

    def do_email_change(self, user, email, activation_key=None):
        """Executes do_email_change_request, returning any resulting error message. """
        try:
            do_email_change_request(user, email, activation_key)
        except ValueError as err:
            return err.message

    def assertFailedRequest(self, response_data, expected_error):
        """Assert that `response_data` indicates a failed request that returns `expected_error`"""
        self.assertFalse(response_data['success'])
        self.assertEquals(expected_error, response_data['error'])
        self.assertFalse(self.user.email_user.called)

    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_duplicate_activation_key(self):
        """Assert that if two users change Email address simultaneously, no error is thrown"""

        # New emails for the users
        user1_new_email = "valid_user1_email@example.com"
        user2_new_email = "valid_user2_email@example.com"

        # Create a another user 'user2' & make request for change email
        user2 = UserFactory.create(email=self.new_email, password="test2")

        # Send requests & ensure no error was thrown
        self.assertIsNone(self.do_email_change(self.user, user1_new_email))
        self.assertIsNone(self.do_email_change(user2, user2_new_email))

    def test_invalid_emails(self):
        """
        Assert the expected error message from the email validation method for an invalid
        (improperly formatted) email address.
        """
        for email in ('bad_email', 'bad_email@', '@bad_email'):
            self.assertEqual(self.do_email_validation(email), 'Valid e-mail address required.')

    def test_change_email_to_existing_value(self):
        """ Test the error message if user attempts to change email to the existing value. """
        self.assertEqual(self.do_email_validation(self.user.email), 'Old email is the same as the new email.')

    def test_duplicate_email(self):
        """
        Assert the expected error message from the email validation method for an email address
        that is already in use by another account.
        """
        UserFactory.create(email=self.new_email)
        self.assertEqual(self.do_email_validation(self.new_email), 'An account with this e-mail already exists.')

    @patch('django.core.mail.send_mail')
    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_email_failure(self, send_mail):
        """ Test the return value if sending the email for the user to click fails. """
        send_mail.side_effect = [Exception, None]
        self.assertEqual(
            self.do_email_change(self.user, "valid@email.com"),
            'Unable to send email activation link. Please try again later.'
        )
        self.assert_no_events_were_emitted()

    @patch('django.core.mail.send_mail')
    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_email_success(self, send_mail):
        """ Test email was sent if no errors encountered. """
        old_email = self.user.email
        new_email = "valid@example.com"
        registration_key = "test registration key"
        self.assertIsNone(self.do_email_change(self.user, new_email, registration_key))
        context = {
            'key': registration_key,
            'old_email': old_email,
            'new_email': new_email
        }
        send_mail.assert_called_with(
            mock_render_to_string('emails/email_change_subject.txt', context),
            mock_render_to_string('emails/email_change.txt', context),
            settings.DEFAULT_FROM_EMAIL,
            [new_email]
        )
        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'email', old=old_email, new=new_email
        )


@patch('django.contrib.auth.models.User.email_user')
@patch('student.views.render_to_response', Mock(side_effect=mock_render_to_response, autospec=True))
@patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
class EmailChangeConfirmationTests(EmailTestMixin, TransactionTestCase):
    """Test that confirmation of email change requests function even in the face of exceptions thrown while sending email"""
    def setUp(self):
        super(EmailChangeConfirmationTests, self).setUp()
        self.user = UserFactory.create()
        self.profile = UserProfile.objects.get(user=self.user)
        self.req_factory = RequestFactory()
        self.request = self.req_factory.get('unused_url')
        self.request.user = self.user
        self.user.email_user = Mock()
        self.pending_change_request = PendingEmailChangeFactory.create(user=self.user)
        self.key = self.pending_change_request.activation_key

    def assertRolledBack(self):
        """Assert that no changes to user, profile, or pending email have been made to the db"""
        self.assertEquals(self.user.email, User.objects.get(username=self.user.username).email)
        self.assertEquals(self.profile.meta, UserProfile.objects.get(user=self.user).meta)
        self.assertEquals(1, PendingEmailChange.objects.count())

    def assertFailedBeforeEmailing(self, email_user):
        """Assert that the function failed before emailing a user"""
        self.assertRolledBack()
        self.assertFalse(email_user.called)

    def check_confirm_email_change(self, expected_template, expected_context):
        """Call `confirm_email_change` and assert that the content was generated as expected

        `expected_template`: The name of the template that should have been used
            to generate the content
        `expected_context`: The context dictionary that should have been used to
            generate the content
        """
        response = confirm_email_change(self.request, self.key)
        self.assertEquals(
            mock_render_to_response(expected_template, expected_context).content,
            response.content
        )

    def assertChangeEmailSent(self, email_user):
        """Assert that the correct email was sent to confirm an email change"""
        context = {
            'old_email': self.user.email,
            'new_email': self.pending_change_request.new_email,
        }
        self.assertEmailUser(
            email_user,
            'emails/email_change_subject.txt',
            context,
            'emails/confirm_email_change.txt',
            context
        )

        # Thorough tests for safe_get_host are elsewhere; here we just want a quick URL sanity check
        request = RequestFactory().post('unused_url')
        request.user = self.user
        request.META['HTTP_HOST'] = "aGenericValidHostName"
        self.append_allowed_hosts("aGenericValidHostName")

        mako_middleware_process_request(request)
        body = render_to_string('emails/confirm_email_change.txt', context)
        url = safe_get_host(request)

        self.assertIn(url, body)

    def test_not_pending(self, email_user):
        self.key = 'not_a_key'
        self.check_confirm_email_change('invalid_email_key.html', {})
        self.assertFailedBeforeEmailing(email_user)

    def test_duplicate_email(self, email_user):
        UserFactory.create(email=self.pending_change_request.new_email)
        self.check_confirm_email_change('email_exists.html', {})
        self.assertFailedBeforeEmailing(email_user)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    def test_old_email_fails(self, email_user):
        email_user.side_effect = [Exception, None]
        self.check_confirm_email_change('email_change_failed.html', {
            'email': self.user.email,
        })
        self.assertRolledBack()
        self.assertChangeEmailSent(email_user)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    def test_new_email_fails(self, email_user):
        email_user.side_effect = [None, Exception]
        self.check_confirm_email_change('email_change_failed.html', {
            'email': self.pending_change_request.new_email
        })
        self.assertRolledBack()
        self.assertChangeEmailSent(email_user)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    def test_successful_email_change(self, email_user):
        self.check_confirm_email_change('email_change_successful.html', {
            'old_email': self.user.email,
            'new_email': self.pending_change_request.new_email
        })
        self.assertChangeEmailSent(email_user)
        meta = json.loads(UserProfile.objects.get(user=self.user).meta)
        self.assertIn('old_emails', meta)
        self.assertEquals(self.user.email, meta['old_emails'][0][0])
        self.assertEquals(
            self.pending_change_request.new_email,
            User.objects.get(username=self.user.username).email
        )
        self.assertEquals(0, PendingEmailChange.objects.count())

    @patch('student.views.PendingEmailChange.objects.get', Mock(side_effect=TestException))
    def test_always_rollback(self, _email_user):
        connection = transaction.get_connection()
        with patch.object(connection, 'rollback', wraps=connection.rollback) as mock_rollback:
            with self.assertRaises(TestException):
                confirm_email_change(self.request, self.key)

            mock_rollback.assert_called_with()

import json
import django.db

from student.tests.factories import UserFactory, RegistrationFactory, PendingEmailChangeFactory
from student.views import reactivation_email_for_user, change_email_request, confirm_email_change
from student.models import UserProfile, PendingEmailChange
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.test.client import RequestFactory
from mock import Mock, patch
from django.http import Http404, HttpResponse
from django.conf import settings
from nose.plugins.skip import SkipTest


class TestException(Exception):
    """Exception used for testing that nothing will catch explicitly"""
    pass


def mock_render_to_string(template_name, context):
    """Return a string that encodes template_name and context"""
    return str((template_name, sorted(context.iteritems())))


def mock_render_to_response(template_name, context):
    """Return an HttpResponse with content that encodes template_name and context"""
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


@patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
@patch('django.contrib.auth.models.User.email_user')
class ReactivationEmailTests(EmailTestMixin, TestCase):
    """Test sending a reactivation email to a user"""

    def setUp(self):
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


class EmailChangeRequestTests(TestCase):
    """Test changing a user's email address"""

    def setUp(self):
        self.user = UserFactory.create()
        self.new_email = 'new.email@edx.org'
        self.req_factory = RequestFactory()
        self.request = self.req_factory.post('unused_url', data={
            'password': 'test',
            'new_email': self.new_email
        })
        self.request.user = self.user
        self.user.email_user = Mock()

    def run_request(self, request=None):
        """Execute request and return result parsed as json

        If request isn't passed in, use self.request instead
        """
        if request is None:
            request = self.request

        response = change_email_request(self.request)
        return json.loads(response.content)

    def assertFailedRequest(self, response_data, expected_error):
        """Assert that `response_data` indicates a failed request that returns `expected_error`"""
        self.assertFalse(response_data['success'])
        self.assertEquals(expected_error, response_data['error'])
        self.assertFalse(self.user.email_user.called)

    def test_unauthenticated(self):
        self.user.is_authenticated = False
        with self.assertRaises(Http404):
            change_email_request(self.request)
        self.assertFalse(self.user.email_user.called)

    def test_invalid_password(self):
        self.request.POST['password'] = 'wrong'
        self.assertFailedRequest(self.run_request(), 'Invalid password')

    def test_invalid_emails(self):
        for email in ('bad_email', 'bad_email@', '@bad_email'):
            self.request.POST['new_email'] = email
            self.assertFailedRequest(self.run_request(), 'Valid e-mail address required.')

    def check_duplicate_email(self, email):
        """Test that a request to change a users email to `email` fails"""
        request = self.req_factory.post('unused_url', data={
            'new_email': email,
            'password': 'test',
        })
        request.user = self.user
        self.assertFailedRequest(self.run_request(request), 'An account with this e-mail already exists.')

    def test_duplicate_email(self):
        UserFactory.create(email=self.new_email)
        self.check_duplicate_email(self.new_email)

    def test_capitalized_duplicate_email(self):
        """Test that we check for email addresses in a case insensitive way"""
        UserFactory.create(email=self.new_email)
        self.check_duplicate_email(self.new_email.capitalize())

    # TODO: Finish testing the rest of change_email_request


@patch('django.contrib.auth.models.User.email_user')
@patch('student.views.render_to_response', Mock(side_effect=mock_render_to_response, autospec=True))
@patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
class EmailChangeConfirmationTests(EmailTestMixin, TransactionTestCase):
    """Test that confirmation of email change requests function even in the face of exceptions thrown while sending email"""
    def setUp(self):
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

    def test_not_pending(self, email_user):
        self.key = 'not_a_key'
        self.check_confirm_email_change('invalid_email_key.html', {})
        self.assertFailedBeforeEmailing(email_user)

    def test_duplicate_email(self, email_user):
        UserFactory.create(email=self.pending_change_request.new_email)
        self.check_confirm_email_change('email_exists.html', {})
        self.assertFailedBeforeEmailing(email_user)

    def test_old_email_fails(self, email_user):
        email_user.side_effect = [Exception, None]
        self.check_confirm_email_change('email_change_failed.html', {
            'email': self.user.email,
        })
        self.assertRolledBack()
        self.assertChangeEmailSent(email_user)

    def test_new_email_fails(self, email_user):
        email_user.side_effect = [None, Exception]
        self.check_confirm_email_change('email_change_failed.html', {
            'email': self.pending_change_request.new_email
        })
        self.assertRolledBack()
        self.assertChangeEmailSent(email_user)

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
    @patch('student.views.transaction.rollback', wraps=django.db.transaction.rollback)
    def test_always_rollback(self, rollback, _email_user):
        with self.assertRaises(TestException):
            confirm_email_change(self.request, self.key)

        rollback.assert_called_with()

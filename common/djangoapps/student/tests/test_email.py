# coding=utf-8
import json
import unittest

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.db import transaction
from django.http import HttpResponse
from django.test import override_settings, TransactionTestCase
from django.test.client import RequestFactory
from mock import Mock, patch
from six import text_type

from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.ace_common.tests.mixins import EmailTemplateTagMixin
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme
from openedx.core.djangoapps.user_api.config.waffle import PREVENT_AUTH_USER_WRITES, SYSTEM_MAINTENANCE_MSG, waffle
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, CacheIsolationMixin
from student.models import (
    PendingEmailChange,
    Registration,
    UserProfile,
)
from openedx.core.lib.request_utils import safe_get_host
from student.tests.factories import PendingEmailChangeFactory, RegistrationFactory, UserFactory
from student.views import (
    SETTING_CHANGE_INITIATED,
    confirm_email_change,
    do_email_change_request,
    validate_new_email
)
from student.views import generate_activation_email_context, send_reactivation_email_for_user
from third_party_auth.views import inactive_user_view
from util.testing import EventTestMixin


class TestException(Exception):
    """
    Exception used for testing that nothing will catch explicitly
    """
    pass


def mock_render_to_string(template_name, context):
    """
    Return a string that encodes template_name and context
    """
    return str((template_name, sorted(context.iteritems())))


def mock_render_to_response(template_name, context):
    """
    Return an HttpResponse with content that encodes template_name and context
    """
    # This simulates any db access in the templates.
    UserProfile.objects.exists()
    return HttpResponse(mock_render_to_string(template_name, context))


class EmailTestMixin(object):
    """
    Adds useful assertions for testing `email_user`
    """

    def assertEmailUser(self, email_user, subject_template, subject_context, body_template, body_context):
        """
        Assert that `email_user` was used to send and email with the supplied subject and body

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
            configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
        )

    def append_allowed_hosts(self, hostname):
        """
        Append hostname to settings.ALLOWED_HOSTS
        """
        settings.ALLOWED_HOSTS.append(hostname)
        self.addCleanup(settings.ALLOWED_HOSTS.pop)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ActivationEmailTests(CacheIsolationTestCase):
    """
    Test sending of the activation email.
    """

    ACTIVATION_SUBJECT = u"Action Required: Activate your {} account".format(settings.PLATFORM_NAME)

    # Text fragments we expect in the body of an email
    # sent from an OpenEdX installation.
    OPENEDX_FRAGMENTS = [
        u"high-quality {platform} courses".format(platform=settings.PLATFORM_NAME),
        "http://edx.org/activate/",
        (
            "please use our web form at "
            u"{support_url} ".format(support_url=settings.SUPPORT_SITE_LINK)
        )
    ]

    def test_activation_email(self):
        self._create_account()
        self._assert_activation_email(self.ACTIVATION_SUBJECT, self.OPENEDX_FRAGMENTS)

    @with_comprehensive_theme("edx.org")
    def test_activation_email_edx_domain(self):
        self._create_account()
        self._assert_activation_email(self.ACTIVATION_SUBJECT, self.OPENEDX_FRAGMENTS)

    def _create_account(self):
        """
        Create an account, triggering the activation email.
        """
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
        """
        Verify that the activation email was sent.
        """
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, subject)
        for fragment in body_fragments:
            self.assertIn(fragment, msg.body)

    def test_do_not_send_email_and_do_activate(self):
        """
        Tests that when an inactive user logs-in using the social auth,
        an activation email is not sent.
        """
        pipeline_partial = {
            'kwargs': {
                'social': {
                    'uid': 'fake uid'
                }
            }
        }
        user = UserFactory(is_active=False)
        Registration().register(user)
        request = RequestFactory().get(settings.SOCIAL_AUTH_INACTIVE_USER_URL)
        request.user = user
        with patch('student.views.management.compose_and_send_activation_email') as email:
            with patch('third_party_auth.provider.Registry.get_from_pipeline') as reg:
                with patch('third_party_auth.pipeline.get', return_value=pipeline_partial):
                    with patch('third_party_auth.pipeline.running', return_value=True):
                        with patch('third_party_auth.is_enabled', return_value=True):
                            reg.skip_email_verification = True
                            inactive_user_view(request)
                            self.assertEquals(user.is_active, True)
                            self.assertEquals(email.called, False, msg='method should not have been called')

    @patch('student.tasks.log')
    def test_send_email_to_inactive_user(self, mock_log):
        """
        Tests that when an inactive user logs-in using the social auth, system
        sends an activation email to the user.
        """
        inactive_user = UserFactory(is_active=False)
        Registration().register(inactive_user)
        request = RequestFactory().get(settings.SOCIAL_AUTH_INACTIVE_USER_URL)
        request.user = inactive_user
        with patch('edxmako.request_context.get_current_request', return_value=request):
            with patch('third_party_auth.pipeline.running', return_value=False):
                inactive_user_view(request)
                mock_log.info.assert_called_with(
                    "Activation Email has been sent to User {user_email}".format(
                        user_email=inactive_user.email
                    )
                )


@patch('student.views.management.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
@patch('django.contrib.auth.models.User.email_user')
class ReactivationEmailTests(EmailTestMixin, CacheIsolationTestCase):
    """
    Test sending a reactivation email to a user
    """

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
        return json.loads(send_reactivation_email_for_user(user).content)

    def assertReactivateEmailSent(self, email_user):
        """
        Assert that the correct reactivation email has been sent
        """
        context = generate_activation_email_context(self.user, self.registration)

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

        with patch('edxmako.request_context.get_current_request', return_value=request):
            body = render_to_string('emails/activation_email.txt', context)
            host = safe_get_host(request)

        self.assertIn(host, body)

    def test_reactivation_email_failure(self, email_user):
        self.user.email_user.side_effect = Exception
        response_data = self.reactivation_email(self.user)

        self.assertReactivateEmailSent(email_user)
        self.assertFalse(response_data['success'])

    def test_reactivation_for_unregistered_user(self, email_user):  # pylint: disable=unused-argument
        """
        Test that trying to send a reactivation email to an unregistered
        user fails without throwing a 500 error.
        """
        response_data = self.reactivation_email(self.unregisteredUser)

        self.assertFalse(response_data['success'])

    def test_reactivation_for_no_user_profile(self, email_user):  # pylint: disable=unused-argument
        """
        Test that trying to send a reactivation email to a user without
        user profile fails without throwing 500 error.
        """
        user = UserFactory.build(username='test_user', email='test_user@test.com')
        user.save()
        response_data = self.reactivation_email(user)
        self.assertFalse(response_data['success'])

    def test_reactivation_email_success(self, email_user):
        response_data = self.reactivation_email(self.user)

        self.assertReactivateEmailSent(email_user)
        self.assertTrue(response_data['success'])


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
class EmailChangeRequestTests(EventTestMixin, EmailTemplateTagMixin, CacheIsolationTestCase):
    """
    Test changing a user's email address
    """

    def setUp(self, tracker='student.views.management.tracker'):
        super(EmailChangeRequestTests, self).setUp(tracker)
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
        """
        Executes validate_new_email, returning any resulting error message.
        """
        try:
            validate_new_email(self.request.user, email)
        except ValueError as err:
            return text_type(err)

    def do_email_change(self, user, email, activation_key=None):
        """
        Executes do_email_change_request, returning any resulting error message.
        """
        with patch('crum.get_current_request', return_value=self.fake_request):
            do_email_change_request(user, email, activation_key)

    def assertFailedRequest(self, response_data, expected_error):
        """
        Assert that `response_data` indicates a failed request that returns `expected_error`
        """
        self.assertFalse(response_data['success'])
        self.assertEquals(expected_error, response_data['error'])
        self.assertFalse(self.user.email_user.called)

    @patch('student.views.management.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_duplicate_activation_key(self):
        """
        Assert that if two users change Email address simultaneously, no error is thrown
        """

        # New emails for the users
        user1_new_email = "valid_user1_email@example.com"
        user2_new_email = "valid_user2_email@example.com"

        # Create a another user 'user2' & make request for change email
        user2 = UserFactory.create(email=self.new_email, password="test2")

        # Send requests & ensure no error was thrown
        self.do_email_change(self.user, user1_new_email)
        self.do_email_change(user2, user2_new_email)

    def test_invalid_emails(self):
        """
        Assert the expected error message from the email validation method for an invalid
        (improperly formatted) email address.
        """
        for email in ('bad_email', 'bad_email@', '@bad_email'):
            self.assertEqual(self.do_email_validation(email), 'Valid e-mail address required.')

    def test_change_email_to_existing_value(self):
        """
        Test the error message if user attempts to change email to the existing value.
        """
        self.assertEqual(self.do_email_validation(self.user.email), 'Old email is the same as the new email.')

    @patch('django.core.mail.send_mail')
    def test_email_failure(self, send_mail):
        """
        Test the return value if sending the email for the user to click fails.
        """
        send_mail.side_effect = [Exception, None]
        with self.assertRaisesRegexp(ValueError, 'Unable to send email activation link. Please try again later.'):
            self.do_email_change(self.user, "valid@email.com")

        self.assert_no_events_were_emitted()

    def test_email_success(self):
        """
        Test email was sent if no errors encountered.
        """
        old_email = self.user.email
        new_email = "valid@example.com"
        registration_key = "test-registration-key"

        self.do_email_change(self.user, new_email, registration_key)

        self._assert_email(
            subject=u'Request to change édX account e-mail',
            body_fragments=[
                u'We received a request to change the e-mail associated with',
                u'your édX account from {old_email} to {new_email}.'.format(
                    old_email=old_email,
                    new_email=new_email,
                ),
                u'If this is correct, please confirm your new e-mail address by visiting:',
                u'http://edx.org/email_confirm/{key}'.format(key=registration_key),
                u'If you didn\'t request this, you don\'t need to do anything;',
                u'you won\'t receive any more email from us.',
                u'Please do not reply to this e-mail; if you require assistance,',
                u'check the help section of the édX web site.',
            ],
        )

        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'email', old=old_email, new=new_email
        )

    def _assert_email(self, subject, body_fragments):
        """
        Verify that the email was sent.
        """
        assert len(mail.outbox) == 1
        assert len(body_fragments) > 1, 'Should provide at least two body fragments'

        message = mail.outbox[0]
        text = message.body
        html = message.alternatives[0][0]

        assert message.subject == subject

        for body in text, html:
            for fragment in body_fragments:
                assert fragment in body


@patch('django.contrib.auth.models.User.email_user')
@patch('student.views.management.render_to_response', Mock(side_effect=mock_render_to_response, autospec=True))
@patch('student.views.management.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
class EmailChangeConfirmationTests(EmailTestMixin, CacheIsolationMixin, TransactionTestCase):
    """
    Test that confirmation of email change requests function even in the face of exceptions thrown while sending email
    """
    def setUp(self):
        super(EmailChangeConfirmationTests, self).setUp()
        self.clear_caches()
        self.addCleanup(self.clear_caches)
        self.user = UserFactory.create()
        self.profile = UserProfile.objects.get(user=self.user)
        self.req_factory = RequestFactory()
        self.request = self.req_factory.get('unused_url')
        self.request.user = self.user
        self.user.email_user = Mock()
        self.pending_change_request = PendingEmailChangeFactory.create(user=self.user)
        self.key = self.pending_change_request.activation_key

    @classmethod
    def setUpClass(cls):
        super(EmailChangeConfirmationTests, cls).setUpClass()
        cls.start_cache_isolation()

    @classmethod
    def tearDownClass(cls):
        cls.end_cache_isolation()
        super(EmailChangeConfirmationTests, cls).tearDownClass()

    def assertRolledBack(self):
        """
        Assert that no changes to user, profile, or pending email have been made to the db
        """
        self.assertEquals(self.user.email, User.objects.get(username=self.user.username).email)
        self.assertEquals(self.profile.meta, UserProfile.objects.get(user=self.user).meta)
        self.assertEquals(1, PendingEmailChange.objects.count())

    def assertFailedBeforeEmailing(self, email_user):
        """
        Assert that the function failed before emailing a user
        """
        self.assertRolledBack()
        self.assertFalse(email_user.called)

    def check_confirm_email_change(self, expected_template, expected_context):
        """
        Call `confirm_email_change` and assert that the content was generated as expected

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
        """
        Assert that the correct email was sent to confirm an email change
        """
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

        with patch('edxmako.request_context.get_current_request', return_value=request):
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

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    def test_prevent_auth_user_writes(self, email_user):  # pylint: disable=unused-argument
        with waffle().override(PREVENT_AUTH_USER_WRITES, True):
            self.check_confirm_email_change('email_change_failed.html', {
                'err_msg': SYSTEM_MAINTENANCE_MSG
            })
            self.assertRolledBack()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @override_settings(MKTG_URLS={'ROOT': 'https://dummy-root', 'CONTACT': '/help/contact-us'})
    def test_marketing_contact_link(self, _email_user):
        context = {
            'site': 'edx.org',
            'old_email': 'old@example.com',
            'new_email': 'new@example.com',
        }

        confirm_email_body = render_to_string('emails/confirm_email_change.txt', context)
        # With marketing site disabled, should link to the LMS contact static page.
        # The http(s) part was omitted keep the test focused.
        self.assertIn('://edx.org/contact', confirm_email_body)

        with patch.dict(settings.FEATURES, {'ENABLE_MKTG_SITE': True}):
            # Marketing site enabled, should link to the marketing site contact page.
            confirm_email_body = render_to_string('emails/confirm_email_change.txt', context)
            self.assertIn('https://dummy-root/help/contact-us', confirm_email_body)

    @patch('student.views.PendingEmailChange.objects.get', Mock(side_effect=TestException))
    def test_always_rollback(self, _email_user):
        connection = transaction.get_connection()
        with patch.object(connection, 'rollback', wraps=connection.rollback) as mock_rollback:
            with self.assertRaises(TestException):
                confirm_email_change(self.request, self.key)

            mock_rollback.assert_called_with()


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
class SecondaryEmailChangeRequestTests(EventTestMixin, EmailTemplateTagMixin, CacheIsolationTestCase):
    """
    Test changing a user's email address
    """

    def setUp(self, tracker='student.views.management.tracker'):
        super(SecondaryEmailChangeRequestTests, self).setUp(tracker)
        self.user = UserFactory.create()
        self.new_secondary_email = 'new.secondary.email@edx.org'
        self.req_factory = RequestFactory()
        self.request = self.req_factory.post('unused_url', data={
            'password': 'test',
            'new_email': self.new_secondary_email
        })
        self.request.user = self.user
        self.user.email_user = Mock()

    def do_email_validation(self, email):
        """
        Executes validate_new_secondary_email, returning any resulting error message.
        """
        try:
            validate_new_email(self.request.user, email)
        except ValueError as err:
            return text_type(err)

    def do_secondary_email_change(self, user, email, activation_key=None):
        """
        Executes do_secondary_email_change_request, returning any resulting error message.
        """
        with patch('crum.get_current_request', return_value=self.fake_request):
            do_email_change_request(
                user=user,
                new_email=email,
                activation_key=activation_key,
                secondary_email_change_request=True
            )

    def assertFailedRequest(self, response_data, expected_error):
        """
        Assert that `response_data` indicates a failed request that returns `expected_error`
        """
        self.assertFalse(response_data['success'])
        self.assertEquals(expected_error, response_data['error'])
        self.assertFalse(self.user.email_user.called)

    def test_invalid_emails(self):
        """
        Assert the expected error message from the email validation method for an invalid
        (improperly formatted) email address.
        """
        for email in ('bad_email', 'bad_email@', '@bad_email'):
            self.assertEqual(self.do_email_validation(email), 'Valid e-mail address required.')

    @patch('django.core.mail.send_mail')
    def test_email_failure(self, send_mail):
        """
        Test the return value if sending the email for the user to click fails.
        """
        send_mail.side_effect = [Exception, None]
        with self.assertRaisesRegexp(ValueError, 'Unable to send email activation link. Please try again later.'):
            self.do_secondary_email_change(self.user, "valid@email.com")

        self.assert_no_events_were_emitted()

    def test_email_success(self):
        """
        Test email was sent if no errors encountered.
        """
        new_email = "valid@example.com"
        registration_key = "test-registration-key"

        self.do_secondary_email_change(self.user, new_email, registration_key)

        self._assert_email(
            subject=u'Request to change édX account secondary e-mail',
            body_fragments=[
                u'We received a request to change the secondary e-mail associated with',
                u'your édX account to {new_email}.'.format(
                    new_email=new_email,
                ),
                u'If this is correct, please confirm your new secondary e-mail address by visiting:',
                u'http://edx.org/activate_secondary_email/{key}'.format(key=registration_key),
                u'If you didn\'t request this, you don\'t need to do anything;',
                u'you won\'t receive any more email from us.',
                u'Please do not reply to this e-mail; if you require assistance,',
                u'check the help section of the édX web site.',
            ],
        )

    def _assert_email(self, subject, body_fragments):
        """
        Verify that the email was sent.
        """
        assert len(mail.outbox) == 1
        assert len(body_fragments) > 1, 'Should provide at least two body fragments'

        message = mail.outbox[0]
        text = message.body
        html = message.alternatives[0][0]

        assert message.subject == subject

        for body in text, html:
            for fragment in body_fragments:
                assert fragment in body

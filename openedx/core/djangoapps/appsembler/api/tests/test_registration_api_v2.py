"""
Tests for openedx.core.djangoapps.appsembler.api.v2.views.RegistrationViewSet

"""
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.permissions import AllowAny

import ddt
from mock import patch

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory

APPSEMBLER_API_VIEWS_MODULE_V2 = 'openedx.core.djangoapps.appsembler.api.v2.views'


@ddt.ddt
@patch(APPSEMBLER_API_VIEWS_MODULE_V2 + '.RegistrationViewSet.authentication_classes', [])
@patch(APPSEMBLER_API_VIEWS_MODULE_V2 + '.RegistrationViewSet.permission_classes', [AllowAny])
@patch(APPSEMBLER_API_VIEWS_MODULE_V2 + '.RegistrationViewSet.throttle_classes', [])
@override_settings(APPSEMBLER_FEATURES={
    'SKIP_LOGIN_AFTER_REGISTRATION': False,
})
class RegistrationApiViewTestsV2(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        # The DRF Router appends '-list' to the base 'registrations' name when
        # registering the endpoint
        self.url = reverse('tahoe-api:v2:registrations-list')
        self.sample_user_data = {
            'username': 'MrRobot',
            'password': 'edX',
            'email': 'mr.robot@example.com',
            'name': 'Mr Robot'
        }

    def test_registration_response(self):
        res = self.client.post(self.url, self.sample_user_data)
        self.assertNotContains(res, "user_id ")
        self.assertContains(res, "user_id", status_code=200)

    @ddt.unpack
    @ddt.data(
        {'send_activation_email': True, 'expected_subject': 'Activate your', 'email_count': 1},
        {'send_activation_email': False, 'expected_subject': None, 'email_count': 0},
        {'send_activation_email': 'True', 'expected_subject': 'Activate your', 'email_count': 1},
        {'send_activation_email': 'False', 'expected_subject': None, 'email_count': 0},
        {'send_activation_email': 'true', 'expected_subject': 'Activate your', 'email_count': 1},
        {'send_activation_email': 'false', 'expected_subject': None, 'email_count': 0},
    )
    def test_send_activation_email_with_password(self, send_activation_email, expected_subject, email_count):
        """
        This test makes sure when the API endpoint is called with a password,
        the send_activation_email parameter is being used properly. Also makes
        sure when the attribute is True the user remains inactive until the
        activation is performed through the activation email. It also makes
        sure the user is automatically activate when the parameter is False.
        """
        params = {
            'username': 'mr_potato_head',
            'email': 'mr_potato_head@example.com',
            'name': 'Mr Potato Head',
            'password': 'some-password',
            'send_activation_email': send_activation_email,
        }

        res = self.client.post(self.url, params)

        self.assertContains(res, 'user_id', status_code=200)
        new_user = User.objects.get(username=params['username'])
        assert new_user.is_active == (not email_count)
        subject = mail.outbox[0].subject if mail.outbox else ''
        assert len(mail.outbox) == email_count, 'Incorrect message count: Subject={}'.format(subject)
        if expected_subject:
            assert expected_subject in mail.outbox[0].subject

    def test_duplicate_identifiers(self):
        self.client.post(self.url, self.sample_user_data)
        res = self.client.post(self.url, {
            'username': self.sample_user_data['username'],
            'password': 'Another Password!',
            'email': 'me@example.com',
            'name': 'The Boss'
        })
        self.assertContains(res, 'Username already exists', status_code=status.HTTP_409_CONFLICT)
        res = self.client.post(self.url, {
            'username': 'world_changer',
            'password': 'Yet Another Password!',
            'email': self.sample_user_data['email'],
            'name': 'World Changer'
        })
        self.assertContains(res, 'Email already exists', status_code=status.HTTP_409_CONFLICT)
        res = self.client.post(self.url, {
            'username': self.sample_user_data['username'],
            'password': 'This Is A Password',
            'email': self.sample_user_data['email'],
            'name': 'Batman'
        })
        self.assertContains(res, 'Both email and username already exist', status_code=status.HTTP_409_CONFLICT)

    def test_similar_username_password(self):
        """
        When username and password are similar, return error msg from UserAttributeSimilarityValidator
        """
        similar_user_data = {
            'username': 'foobar',
            'password': 'foobar',
            'email': 'mr.robot@example.com',
            'name': 'Mr Robot'
        }
        res = self.client.post(self.url, similar_user_data)
        self.assertContains(res, "The password is too similar to the username.", status_code=status.HTTP_400_BAD_REQUEST)

    def test_happy_path(self):
        assert not mail.outbox, 'Should not have any messages'
        res = self.client.post(self.url, self.sample_user_data)
        self.assertContains(res, 'user_id', status_code=200)
        assert mail.outbox, 'Should send the activation email'
        email = mail.outbox[0]
        assert 'Activate' in email.subject, 'Should have the activation email subject'
        assert '/activate/' in email.body, 'Should include the activation link in the body'

    def test_without_password_field(self):
        params = {
            'username': 'mr_potato_head',
            'email': 'mr_potato_head@example.com',
            'name': 'Mr Potato Head',
        }
        with patch('openedx.core.djangoapps.user_authn.views.password_reset.get_current_site',
                   return_value=self.site):
            res = self.client.post(self.url, params)
        self.assertContains(res, 'user_id', status_code=status.HTTP_200_OK)

    @ddt.data(
        {'send_activation_email': True},
        {'send_activation_email': 'True'},
        {'send_activation_email': 'true'},
        {'send_activation_email': False},
        {'send_activation_email': 'False'},
        {'send_activation_email': 'false'},
        {},
    )
    def test_send_activation_email_without_password(self, activation_email_params):
        """
        Should not send the activation email. Ignores the `send_activation_email` param. It
        also makes sure the user remains inactive (is_active=False). The user
        will be activated after the password is reseted.
        """
        params = {
            'username': 'mr_potato_head',
            'email': 'mr_potato_head@example.com',
            'name': 'Mr Potato Head',
        }
        params.update(activation_email_params)

        with patch('openedx.core.djangoapps.user_authn.views.password_reset.get_current_site',
                   return_value=self.site):
            res = self.client.post(self.url, params)

        self.assertContains(res, 'user_id', status_code=200)
        new_user = User.objects.get(username=params['username'])
        assert not new_user.is_active
        assert mail.outbox, 'Should send the password reset email'

        assert len(mail.outbox) == 1, ('Send NOT password reset email but NOT activation.\n'
                                       'Subjects={subjects}.\n'
                                       'params]}').format(
            subjects=[email.subject for email in mail.outbox],
            params=params,
        )

        email = mail.outbox[0]
        assert 'Password reset on' in email.subject

    @ddt.unpack
    @ddt.data(
        {'missing_field': 'username', 'error_message': 'Username must be between'},
        {'missing_field': 'name', 'error_message': 'Your legal name must be a minimum of one'},
    )
    def test_missing_field(self, missing_field, error_message):
        params = self.sample_user_data.copy()
        del params[missing_field]
        res = self.client.post(self.url, params)
        body = res.content.decode('utf-8')
        assert res.status_code == 400, 'Should fail with 400 error: {}'.format(body)
        assert error_message in body, 'Should fail with 400 error: {}'.format(body)

    @ddt.unpack
    @ddt.data(
        {'invalid_field': 'username', 'error_message': 'Usernames can only contain letters'},
        {'invalid_field': 'email', 'error_message': 'A properly formatted e-mail is required'},
    )
    def test_incorrect_field_format(self, invalid_field, error_message):
        params = self.sample_user_data.copy()
        params[invalid_field] = '%%%%%%%'
        res = self.client.post(self.url, params)
        body = res.content.decode('utf-8')
        assert res.status_code == 400, 'Should fail with 400 error: {}'.format(body)
        assert error_message in body, 'Should fail with 400 error: {}'.format(body)

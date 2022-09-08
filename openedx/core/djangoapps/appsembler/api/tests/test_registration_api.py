"""
Tests for openedx.core.djangoapps.appsembler.api.views.RegistrationViewSet

These tests adapted from Appsembler enterprise `appsembler_api` tests

"""
from django.urls import reverse
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny

import ddt
from mock import patch

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory

APPSEMBLER_API_VIEWS_MODULE = 'openedx.core.djangoapps.appsembler.api.v1.views'


@ddt.ddt
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.authentication_classes', [])
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.permission_classes', [AllowAny])
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.throttle_classes', [])
class RegistrationApiViewTests(TestCase):
    def setUp(self):

        self.site = SiteFactory()
        # The DRF Router appends '-list' to the base 'registrations' name when
        # registering the endpoint
        self.url = reverse('tahoe-api:v1:registrations-list')
        self.sample_user_data = {
            'username': 'MrRobot',
            'password': 'edX',
            'email': 'mr.robot@example.com',
            'name': 'Mr Robot'
        }

    def test_happy_path(self):
        assert not mail.outbox, 'Should not have any messages'
        res = self.client.post(self.url, self.sample_user_data)
        self.assertContains(res, 'user_id', status_code=200)
        assert mail.outbox, 'Should send the activation email'
        email = mail.outbox[0]
        assert 'Activate' in email.subject, 'Should have the activation email subject'
        assert '/activate/' in email.body, 'Should include the activation link in the body'

    def test_duplicate_identifiers(self):
        self.client.post(self.url, self.sample_user_data)
        res = self.client.post(self.url, {
            'username': self.sample_user_data['username'],
            'password': 'Another Password!',
            'email': 'me@example.com',
            'name': 'The Boss'
        })
        self.assertContains(res, 'User already exists', status_code=status.HTTP_409_CONFLICT)
        res = self.client.post(self.url, {
            'username': 'world_changer',
            'password': 'Yet Another Password!',
            'email': self.sample_user_data['email'],
            'name': 'World Changer'
        })
        self.assertContains(res, 'User already exists', status_code=status.HTTP_409_CONFLICT)

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
        {'send_activation_email': True, 'expected_subject': 'Activate your', 'email_count': 1},
        {'send_activation_email': 'True', 'expected_subject': 'Activate your', 'email_count': 1},
        {'send_activation_email': 'true', 'expected_subject': 'Activate your', 'email_count': 1},
        {'send_activation_email': False, 'expected_subject': None, 'email_count': 0},
        {'send_activation_email': 'False', 'expected_subject': None, 'email_count': 0},
        {'send_activation_email': 'false', 'expected_subject': None, 'email_count': 0},
    )
    @ddt.unpack
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

    @ddt.data('username', 'name')
    def test_missing_field(self, field):
        params = self.sample_user_data.copy()
        del params[field]
        res = self.client.post(self.url, params)
        self.assertContains(
            res, 'Invalid parameters on user creation', status_code=400)

    @ddt.data('username', 'email')
    def test_incorrect_field_format(self, field):
        params = self.sample_user_data.copy()
        params[field] = '%%%%%%%'
        res = self.client.post(self.url, params)
        self.assertContains(
            res, 'Invalid parameters on user creation', status_code=400)

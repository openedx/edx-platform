"""
Tests for openedx.core.djangoapps.appsembler.api.views.RegistrationViewSet

These tests adapted from Appsembler enterprise `appsembler_api` tests

"""
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny

import ddt
from mock import patch

APPSEMBLER_API_VIEWS_MODULE = 'openedx.core.djangoapps.appsembler.api.v1.views'


@ddt.ddt
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.authentication_classes', [])
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.permission_classes', [AllowAny])
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.throttle_classes', [])
@override_settings(APPSEMBLER_FEATURES={
    'SKIP_LOGIN_AFTER_REGISTRATION': False,
})
class RegistrationApiViewTests(TestCase):
    def setUp(self):

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
        res = self.client.post(self.url, self.sample_user_data)
        self.assertContains(res, 'user_id', status_code=200)

    def test_duplicate_identifiers(self):
        self.client.post(self.url, self.sample_user_data)

        res = self.client.post(self.url, {
            'username': self.sample_user_data['username'],
            'password': 'Another Password!',
            'email': 'me@example.com',
            'name': 'The Boss'
        })
        self.assertContains(res, 'User already exists', status_code=409)

        res = self.client.post(self.url, {
            'username': 'world_changer',
            'password': 'Yet Another Password!',
            'email': self.sample_user_data['email'],
            'name': 'World Changer'
        })
        self.assertContains(res, 'User already exists', status_code=409)

    def test_without_password_field(self):
        params = {
            'username': 'mr_potato_head',
            'email': 'mr_potato_head@example.com',
            'name': 'Mr Potato Head',
        }
        res = self.client.post(self.url, params)
        self.assertContains(res, 'user_id', status_code=200)

    @ddt.data(True, False, 'True', 'False', 'true', 'false')
    def test_send_activation_email_with_password(self, send_activation_email):
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

        def fake_send(user, profile, user_registration=None):
            assert send_activation_email in [True, 'True', 'true'], 'activation email should not be called'

        with patch('student.views.management.compose_and_send_activation_email', fake_send):
            res = self.client.post(self.url, params)
            self.assertContains(res, 'user_id', status_code=200)
            new_user = User.objects.get(username=params['username'])
            if send_activation_email in [False, 'False', 'false']:
                self.assertTrue(new_user.is_active)
            else:
                self.assertFalse(new_user.is_active)

    @ddt.data(True, False, 'True', 'False', 'true', 'false')
    def test_send_activation_email_without_password(self, send_activation_email):
        """
        Should not send email. Ignores the `send_activation_email` param. It
        also makes sure the user remains inactive (is_active=False). The user
        will be activated after the password is reseted.
        """
        params = {
            'username': 'mr_potato_head',
            'email': 'mr_potato_head@example.com',
            'name': 'Mr Potato Head',
            'send_activation_email': send_activation_email,
        }

        def fake_send(user, profile, user_registration=None):
            assert False, 'Should not call fake_send when no password'

        with patch('openedx.core.djangoapps.user_authn.views.password_reset.get_current_site',
                   return_value=self.site):
            with patch('student.views.management.compose_and_send_activation_email', fake_send):
                res = self.client.post(self.url, params)
                self.assertContains(res, 'user_id', status_code=200)
                new_user = User.objects.get(username=params['username'])
                assert not new_user.is_active

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

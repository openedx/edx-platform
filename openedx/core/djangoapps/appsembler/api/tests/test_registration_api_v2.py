"""
Tests for openedx.core.djangoapps.appsembler.api.v2.views.RegistrationViewSet

"""
from django.contrib.auth.models import User
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
        {'send_activation_email': True, 'should_send': True},
        {'send_activation_email': False, 'should_send': False},
        {'send_activation_email': 'True', 'should_send': True},
        {'send_activation_email': 'False', 'should_send': False},
        {'send_activation_email': 'true', 'should_send': True},
        {'send_activation_email': 'false', 'should_send': False},
    )
    def test_send_activation_email_with_password(self, send_activation_email, should_send):
        """
        This test makes sure when the API endpoint is called with a password,
        the send_activation_email parameter is being used properly. Also makes
        sure when the attribute is True the user remains inactive until the
        activation is performed through the activation email. It also makes
        sure the user is automatically activate when the parameter is False.

        TODO: Reuse the tests of v1's RegistrationApiViewTests instead of duplicating code
              as described in https://github.com/appsembler/edx-platform/issues/1047
        """
        params = {
            'username': 'mr_potato_head',
            'email': 'mr_potato_head@example.com',
            'name': 'Mr Potato Head',
            'password': 'some-password',
            'send_activation_email': send_activation_email,
        }

        with patch('openedx.core.djangoapps.user_authn.views.register.compose_and_send_activation_email') as fake_send:
            res = self.client.post(self.url, params)
            self.assertContains(res, 'user_id', status_code=200)
            new_user = User.objects.get(username=params['username'])

            assert fake_send.called == should_send, 'activation email should not be called'
            assert new_user.is_active == (not should_send), 'xor, Either activate or send the email'

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

"""
Tests for openedx.core.djangoapps.appsembler.api.views.RegistrationViewSet

These tests adapted from Appsembler enterprise `appsembler_api` tests

"""
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.permissions import AllowAny

import ddt
from mock import patch

APPSEMBLER_API_VIEWS_MODULE = 'openedx.core.djangoapps.appsembler.api.v1.views'


@ddt.ddt
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.authentication_classes', [])
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.permission_classes', [AllowAny])
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

    def test_with_enable_activation_email(self):
        params = {
            'username': 'mr_potato_head',
            'email': 'mr_potato_head@example.com',
            'name': 'Mr Potato Head',
            'send_activation_email': True,
        }
        res = self.client.post(self.url, params)
        self.assertContains(res, 'user_id', status_code=200)

    def test_with_disable_activation_email(self):
        params = {
            'username': 'mr_potato_head',
            'email': 'mr_potato_head@example.com',
            'name': 'Mr Potato Head',
            'send_activation_email': False,
        }
        res = self.client.post(self.url, params)
        self.assertContains(res, 'user_id', status_code=200)

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

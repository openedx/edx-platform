"""
Tests for openedx.core.djangoapps.appsembler.api.v2.views.RegistrationViewSet

"""
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

"""
Tests throttling (rate limiting) for the Tahoe API
"""

from django.conf import settings
from django.urls import reverse
from django.test.utils import override_settings

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.test import APITestCase

import ddt
from mock import patch
import unittest

from openedx.core.djangoapps.appsembler.api.permissions import TahoeAPIUserThrottle

APPSEMBLER_API_VIEWS_MODULE = 'openedx.core.djangoapps.appsembler.api.v1.views'


def make_post_data(val):
    """
    val is some unique idetifier, typically an integer
    """
    return dict(
        name='Joe Bob-{}'.format(val),
        username='joebob{}'.format(val),
        email='joebob-{}@example.com'.format(val)
    )


@ddt.ddt
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.authentication_classes', [])
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.permission_classes', [AllowAny])
@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'general': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'mongo_metadata_inheritance': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'loc_cache': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'course_structure_cache': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
})
class TahoeApiThrotteTest(APITestCase):
    def setUp(self):
        self.url = reverse('tahoe-api:v1:registrations-list')
        self.rate_limit, self.rate_limit_unit = TahoeAPIUserThrottle.rate.split('/')
        self.rate_limit = int(self.rate_limit)
        assert self.rate_limit_unit == 'minute'

    @unittest.skipIf(settings.TAHOE_ALWAYS_SKIP_TEST, 'Skipped due to unknown failures')
    def test_throttle_with_registration_api(self):
        """
        This test is skipped because it causes the following in the post:

            TransactionManagementError: An error occurred in the current
            transaction. You can't execute queries until the end of the
            'atomic' block.

        This needs investigation.
        """
        for attempt in range(self.rate_limit):
            post_data = make_post_data(attempt)
            response = self.client.post(self.url, post_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        post_data = make_post_data(self.rate_limit)
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

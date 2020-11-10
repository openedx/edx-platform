"""Tests for disabling rate limiting. """


import unittest

import mock
from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from rest_framework.exceptions import Throttled
from rest_framework.throttling import BaseThrottle
from rest_framework.views import APIView

from common.djangoapps.util.disable_rate_limit import can_disable_rate_limit
from common.djangoapps.util.models import RateLimitConfiguration


class FakeThrottle(BaseThrottle):
    def allow_request(self, request, view):
        return False


@can_disable_rate_limit
class FakeApiView(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [FakeThrottle]


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class DisableRateLimitTest(TestCase):
    """Check that we can disable rate limiting for perf testing. """

    def setUp(self):
        super(DisableRateLimitTest, self).setUp()
        cache.clear()
        self.view = FakeApiView()

    def test_enable_rate_limit(self):
        # Enable rate limiting using model-based config
        RateLimitConfiguration.objects.create(enabled=True)

        # By default, should enforce rate limiting
        # Since our fake throttle always rejects requests,
        # we should expect the request to be rejected.
        request = mock.Mock()
        with self.assertRaises(Throttled):
            self.view.check_throttles(request)

    def test_disable_rate_limit(self):
        # Disable rate limiting using model-based config
        RateLimitConfiguration.objects.create(enabled=False)

        # With rate-limiting disabled, the request
        # should get through.  The `check_throttles()` call
        # should return without raising an exception.
        request = mock.Mock()
        self.view.check_throttles(request)

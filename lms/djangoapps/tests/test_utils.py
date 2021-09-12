"""
Unit Tests for Utils Class
"""


from unittest import TestCase

import ddt
from django.conf import settings
from opaque_keys.edx.keys import CourseKey, UsageKey

from lms.djangoapps.utils import _get_key


@ddt.ddt
class UtilsTests(TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    @ddt.data(
        ['edX/DemoX/Demo_Course', CourseKey.from_string('edX/DemoX/Demo_Course'), CourseKey],
        ['course-v1:edX+DemoX+Demo_Course', CourseKey.from_string('course-v1:edX+DemoX+Demo_Course'), CourseKey],
        [CourseKey.from_string('course-v1:edX+DemoX+Demo_Course'),
         CourseKey.from_string('course-v1:edX+DemoX+Demo_Course'), CourseKey],
        ['block-v1:edX+DemoX+Demo_Course+type@sequential+block@workflow',
         UsageKey.from_string('block-v1:edX+DemoX+Demo_Course+type@sequential+block@workflow'), UsageKey],
        [UsageKey.from_string('block-v1:edX+DemoX+Demo_Course+type@sequential+block@workflow'),
         UsageKey.from_string('block-v1:edX+DemoX+Demo_Course+type@sequential+block@workflow'), UsageKey],
    )
    @ddt.unpack
    def test_get_key(self, input_key, output_key, key_cls):
        assert _get_key(input_key, key_cls) == output_key

    def test_same_site_cookie_version(self):
        """
        Make sure with django (2.2 or 3.0) django_cookies_samesite settings enabled.
        For greater version django_cookies_samesite not required.
        """
        # not adding any django condition here. it will fail with django31 which is fine for now.
        self.assertTrue('django_cookies_samesite.middleware.CookiesSameSite' in settings.MIDDLEWARE)
        self.assertTrue(hasattr(settings, 'DCS_SESSION_COOKIE_SAMESITE_FORCE_ALL'))
        self.assertTrue(hasattr(settings, 'DCS_SESSION_COOKIE_SAMESITE'))

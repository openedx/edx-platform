# -*- coding: utf-8 -*-
"""
Tests for mobile API utilities.
"""

import ddt
from django.test import TestCase
from mobile_api.models import MobileApiConfig

from .utils import mobile_course_access, mobile_view


@ddt.ddt
class TestMobileAPIDecorators(TestCase):
    """
    Basic tests for mobile api decorators to ensure they retain the docstrings.
    """
    @ddt.data(mobile_view, mobile_course_access)
    def test_function_decorator(self, decorator):
        @decorator()
        def decorated_func():
            """
            Test docstring of decorated function.
            """
            pass

        self.assertIn("Test docstring of decorated function.", decorated_func.__doc__)
        self.assertEquals(decorated_func.__name__, "decorated_func")
        self.assertTrue(decorated_func.__module__.endswith("tests"))


class TestMobileApiConfig(TestCase):
    """
    Tests MobileAPIConfig
    """

    def test_video_profile_list(self):
        """Check that video_profiles config is returned in order as a list"""
        MobileApiConfig(video_profiles="mobile_low,mobile_high,youtube").save()
        video_profile_list = MobileApiConfig.get_video_profiles()
        self.assertEqual(
            video_profile_list,
            [u'mobile_low', u'mobile_high', u'youtube']
        )

    def test_video_profile_list_with_whitespace(self):
        """Check video_profiles config with leading and trailing whitespace"""
        MobileApiConfig(video_profiles=" mobile_low , mobile_high,youtube ").save()
        video_profile_list = MobileApiConfig.get_video_profiles()
        self.assertEqual(
            video_profile_list,
            [u'mobile_low', u'mobile_high', u'youtube']
        )

    def test_empty_video_profile(self):
        """Test an empty video_profile"""
        MobileApiConfig(video_profiles="").save()
        video_profile_list = MobileApiConfig.get_video_profiles()
        self.assertEqual(video_profile_list, [])

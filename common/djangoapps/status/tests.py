# -*- coding: utf-8 -*-
""" Tests for setting and displaying the site status message. """
import ddt
import unittest

from django.test import TestCase
from django.core.cache import cache
from django.conf import settings
from opaque_keys.edx.locations import CourseLocator

from .status import get_site_status_msg
from .models import GlobalStatusMessage, CourseMessage


@ddt.ddt
class TestStatus(TestCase):
    """Test that the get_site_status_msg function does the right thing"""

    def setUp(self):
        super(TestStatus, self).setUp()
        # Clear the cache between test runs.
        cache.clear()
        self.course_key = CourseLocator(org='TestOrg', course='TestCourse', run='TestRun')

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @ddt.data(
        ("Test global message", "Test course message"),
        (u" Ŧɇsŧ sŧȺŧᵾs", u"Ṫëṡẗ ċöüṛṡë ṡẗäẗüṡ "),
        (u"", u"Ṫëṡẗ ċöüṛṡë ṡẗäẗüṡ "),
        (u" Ŧɇsŧ sŧȺŧᵾs", u""),
    )
    @ddt.unpack
    def test_get_site_status_msg(self, test_global_message, test_course_message):
        """Test status messages in a variety of situations."""

        # When we don't have any data set.
        self.assertEqual(get_site_status_msg(None), None)
        self.assertEqual(get_site_status_msg(self.course_key), None)

        msg = GlobalStatusMessage.objects.create(message=test_global_message, enabled=True)
        msg.save()

        self.assertEqual(get_site_status_msg(None), test_global_message)

        course_msg = CourseMessage.objects.create(
            global_message=msg, message=test_course_message, course_key=self.course_key
        )
        course_msg.save()
        self.assertEqual(
            get_site_status_msg(self.course_key),
            u"{} <br /> {}".format(test_global_message, test_course_message)
        )

        msg = GlobalStatusMessage.objects.create(message="", enabled=False)
        msg.save()

        self.assertEqual(get_site_status_msg(None), None)
        self.assertEqual(get_site_status_msg(self.course_key), None)

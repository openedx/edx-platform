"""
Tests for course utils.
"""

from django.test import TestCase, override_settings
import mock
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from util.course import get_lms_link_for_about_page


class LmsLinksTestCase(TestCase):
    """ Tests for LMS links. """

    def test_about_page(self):
        """ Get URL for about page, no marketing site """
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': False}):
            self.assertEquals(self.get_about_page_link(), "http://localhost:8000/courses/mitX/101/test/about")

    @override_settings(MKTG_URLS={'ROOT': 'https://dummy-root'})
    def test_about_page_marketing_site(self):
        """ Get URL for about page, marketing root present. """
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True}):
            self.assertEquals(self.get_about_page_link(), "https://dummy-root/courses/mitX/101/test/about")
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': False}):
            self.assertEquals(self.get_about_page_link(), "http://localhost:8000/courses/mitX/101/test/about")

    @override_settings(MKTG_URLS={'ROOT': 'https://www.dummyhttps://x'})
    def test_about_page_marketing_site_https__edge(self):
        """ Get URL for about page """
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True}):
            self.assertEquals(self.get_about_page_link(), "https://www.dummyhttps://x/courses/mitX/101/test/about")

    def get_about_page_link(self):
        """ create mock course and return the about page link."""
        course_key = SlashSeparatedCourseKey('mitX', '101', 'test')
        return get_lms_link_for_about_page(course_key)

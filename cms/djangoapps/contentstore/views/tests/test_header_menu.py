#-*- coding: utf-8 -*-

"""
Course Header Menu Tests.
"""


from django.conf import settings
from django.test.utils import override_settings

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.utils import reverse_course_url
from common.djangoapps.util.testing import UrlResetMixin

FEATURES_WITH_CERTS_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_ENABLED['CERTIFICATES_HTML_VIEW'] = True

FEATURES_WITH_EXAM_SETTINGS_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_EXAM_SETTINGS_ENABLED['ENABLE_EXAM_SETTINGS_HTML_VIEW'] = True

FEATURES_WITH_EXAM_SETTINGS_DISABLED = settings.FEATURES.copy()
FEATURES_WITH_EXAM_SETTINGS_DISABLED['ENABLE_EXAM_SETTINGS_HTML_VIEW'] = False


@override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
class TestHeaderMenu(CourseTestCase, UrlResetMixin):
    """
    Unit tests for the course header menu.
    """
    def setUp(self):
        """
        Set up the for the course header menu tests.
        """
        super(TestHeaderMenu, self).setUp()
        self.reset_urls()

    def test_header_menu_without_web_certs_enabled(self):
        """
        Tests course header menu should not have `Certificates` menu item
        if course has not web/HTML certificates enabled.
        """
        self.course.cert_html_view_enabled = False
        self.save_course()
        outline_url = reverse_course_url('course_handler', self.course.id)
        resp = self.client.get(outline_url, HTTP_ACCEPT='text/html')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, '<li class="nav-item nav-course-settings-certificates">')

    def test_header_menu_with_web_certs_enabled(self):
        """
        Tests course header menu should have `Certificates` menu item
        if course has web/HTML certificates enabled.
        """
        outline_url = reverse_course_url('course_handler', self.course.id)
        resp = self.client.get(outline_url, HTTP_ACCEPT='text/html')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<li class="nav-item nav-course-settings-certificates">')

    @override_settings(FEATURES=FEATURES_WITH_EXAM_SETTINGS_DISABLED)
    def test_header_menu_without_exam_settings_enabled(self):
        """
        Tests course header menu should not have `Exam Settings` menu item
        if course does not have the Exam Settings view enabled.
        """
        outline_url = reverse_course_url('course_handler', self.course.id)
        resp = self.client.get(outline_url, HTTP_ACCEPT='text/html')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, '<li class="nav-item nav-course-settings-exams">')

    @override_settings(FEATURES=FEATURES_WITH_EXAM_SETTINGS_ENABLED)
    def test_header_menu_with_exam_settings_enabled(self):
        """
        Tests course header menu should have `Exam Settings` menu item
        if course does have Exam Settings view enabled.
        """
        outline_url = reverse_course_url('course_handler', self.course.id)
        resp = self.client.get(outline_url, HTTP_ACCEPT='text/html')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<li class="nav-item nav-course-settings-exams">')

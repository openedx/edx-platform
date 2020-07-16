#-*- coding: utf-8 -*-

"""
Exam Settings View Tests
"""

import ddt

from django.conf import settings
from django.test.utils import override_settings

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url
from util.testing import UrlResetMixin

FEATURES_WITH_CERTS_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_ENABLED['CERTIFICATES_HTML_VIEW'] = True

FEATURES_WITH_EXAM_SETTINGS_ENABLED = FEATURES_WITH_CERTS_ENABLED.copy()
FEATURES_WITH_EXAM_SETTINGS_ENABLED['ENABLE_EXAM_SETTINGS_HTML_VIEW'] = True

FEATURES_WITH_EXAM_SETTINGS_DISABLED = FEATURES_WITH_CERTS_ENABLED.copy()
FEATURES_WITH_EXAM_SETTINGS_DISABLED['ENABLE_EXAM_SETTINGS_HTML_VIEW'] = False


@ddt.ddt
class TestExamSettingsView(CourseTestCase, UrlResetMixin):
    """
    Unit tests for the exam settings view.
    """
    def setUp(self):
        """
        Set up the for the exam settings view tests.
        """
        super(TestExamSettingsView, self).setUp()
        self.reset_urls()

    @override_settings(FEATURES=FEATURES_WITH_EXAM_SETTINGS_DISABLED)
    @ddt.data(
        "certificates_list_handler",
        "settings_handler",
        "group_configurations_list_handler",
        "grading_handler",
        "advanced_settings_handler"
    )
    def test_view_without_exam_settings_enabled(self, handler):
        """
        Tests pages should not have `Exam Settings` item
        if course does not have the Exam Settings view enabled.
        """
        outline_url = reverse_course_url(handler, self.course.id)
        resp = self.client.get(outline_url, HTTP_ACCEPT='text/html')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'Proctored Exam Settings')

    @override_settings(FEATURES=FEATURES_WITH_EXAM_SETTINGS_ENABLED)
    @ddt.data(
        "certificates_list_handler",
        "settings_handler",
        "group_configurations_list_handler",
        "grading_handler",
        "advanced_settings_handler"
    )
    def test_view_with_exam_settings_enabled(self, handler):
        """
        Tests pages should have `Exam Settings` item
        if course does have Exam Settings view enabled.
        """
        outline_url = reverse_course_url(handler, self.course.id)
        resp = self.client.get(outline_url, HTTP_ACCEPT='text/html')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Proctored Exam Settings')

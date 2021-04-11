#-*- coding: utf-8 -*-

"""
Exam Settings View Tests
"""

import ddt
import lxml
from django.conf import settings
from django.test.utils import override_settings

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.utils import reverse_course_url
from common.djangoapps.util.testing import UrlResetMixin

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

    @staticmethod
    def _get_exam_settings_alert_text(raw_html_content):
        """ Get text content of alert banner """
        parsed_html = lxml.html.fromstring(raw_html_content)
        alert_nodes = parsed_html.find_class('exam-settings-alert')
        assert len(alert_nodes) == 1
        alert_node = alert_nodes[0]
        return alert_node.text_content()

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

    @override_settings(
        PROCTORING_BACKENDS={
            'DEFAULT': 'test_proctoring_provider',
            'proctortrack': {}
        },
        FEATURES=FEATURES_WITH_EXAM_SETTINGS_ENABLED,
    )
    @ddt.data(
        "advanced_settings_handler",
        "course_handler",
    )
    def test_exam_settings_alert_with_exam_settings_enabled(self, page_handler):
        """
        An alert should appear if current exam settings are invalid.
        The exam settings alert should direct users to the exam settings page.
        """
        # create an error by setting proctortrack as the provider and not setting
        # the (required) escalation contact
        self.course.proctoring_provider = 'proctortrack'
        self.save_course()

        url = reverse_course_url(page_handler, self.course.id)
        resp = self.client.get(url, HTTP_ACCEPT='text/html')
        alert_text = self._get_exam_settings_alert_text(resp.content)
        assert (
            'This course has proctored exam settings that are incomplete or invalid.'
            in alert_text
        )
        assert (
            'To update these settings go to the Proctored Exam Settings page.'
            in alert_text
        )

    @override_settings(
        PROCTORING_BACKENDS={
            'DEFAULT': 'test_proctoring_provider',
            'proctortrack': {}
        },
        FEATURES=FEATURES_WITH_EXAM_SETTINGS_DISABLED,
    )
    @ddt.data(
        "advanced_settings_handler",
        "course_handler",
    )
    def test_exam_settings_alert_with_exam_settings_disabled(self, page_handler):
        """
        An alert should appear if current exam settings are invalid.
        The exam settings alert should direct users to the advanced settings page
        if the exam settings feature is not available.
        """
        # create an error by setting proctortrack as the provider and not setting
        # the (required) escalation contact
        self.course.proctoring_provider = 'proctortrack'
        self.save_course()

        url = reverse_course_url(page_handler, self.course.id)
        resp = self.client.get(url, HTTP_ACCEPT='text/html')
        alert_text = self._get_exam_settings_alert_text(resp.content)
        assert (
            'This course has proctored exam settings that are incomplete or invalid.'
            in alert_text
        )
        self.maxDiff = None
        if page_handler == 'advanced_settings_handler':
            assert (
                'You will be unable to make changes until the following settings are updated on the page below.'
                in alert_text
            )
        else:
            assert 'To update these settings go to the Advanced Settings page.' in alert_text

    @ddt.data(
        "advanced_settings_handler",
        "course_handler",
    )
    def test_exam_settings_alert_not_shown(self, page_handler):
        """
        Alert should not be visible if no proctored exam setting error exists
        """
        url = reverse_course_url(page_handler, self.course.id)
        resp = self.client.get(url, HTTP_ACCEPT='text/html')
        parsed_html = lxml.html.fromstring(resp.content)
        alert_nodes = parsed_html.find_class('exam-settings-alert')
        assert len(alert_nodes) == 0

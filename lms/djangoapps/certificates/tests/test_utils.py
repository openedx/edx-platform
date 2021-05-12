"""
Tests for Certificates app utility functions
"""
from unittest.mock import patch

from django.test import TestCase

from lms.djangoapps.certificates.utils import has_html_certificates_enabled
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


class CertificateUtilityTests(TestCase):
    """
    Tests for course certificate utility functions
    """
    def setUp(self):
        super().setUp()
        self.course_overview = CourseOverviewFactory.create()

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': False})
    def test_has_html_certificates_enabled_from_course_overview_cert_html_view_disabled(self):
        """
        Test to ensure we return the correct value when the `CERTIFICATES_HTML_VIEW` setting is disabled.
        """
        assert not has_html_certificates_enabled(self.course_overview)

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_has_html_certificates_enabled_from_course_overview_enabled(self):
        """
        Test to ensure we return the correct value when the HTML certificates are enabled in a course-run.
        """
        self.course_overview.cert_html_view_enabled = True
        self.course_overview.save()

        assert has_html_certificates_enabled(self.course_overview)

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_has_html_certificates_enabled_from_course_overview_disabled(self):
        """
        Test to ensure we return the correct value when the HTML certificates are disabled in a course-run.
        """
        self.course_overview.cert_html_view_enabled = False
        self.course_overview.save()

        assert not has_html_certificates_enabled(self.course_overview)

"""
Tests for help_context_processor.py
"""

import ConfigParser
from mock import patch

from django.conf import settings
from django.test import TestCase

from util.help_context_processor import common_doc_url


CONFIG_FILE = open(settings.REPO_ROOT / "docs" / "lms_config.ini")
CONFIG = ConfigParser.ConfigParser()
CONFIG.readfp(CONFIG_FILE)


class HelpContextProcessorTest(TestCase):
    """
    Tests for help_context_processor.py
    """

    def setUp(self):
        super(HelpContextProcessorTest, self).setUp()

    @staticmethod
    def _get_doc_url(page_token=None):
        """ Helper method for getting the doc url. """
        return common_doc_url(None, CONFIG)['get_online_help_info'](page_token)['doc_url']

    @staticmethod
    def _get_pdf_url():
        """ Helper method for getting the pdf url. """
        return common_doc_url(None, CONFIG)['get_online_help_info']()['pdf_url']

    def test_get_doc_url(self):
        # Test default values.
        self.assertEqual(
            "http://edx.readthedocs.io/projects/open-edx-learner-guide/en/latest/index.html",
            HelpContextProcessorTest._get_doc_url()
        )

        # Provide a known page_token.
        self.assertEqual(
            "http://edx.readthedocs.io/projects/open-edx-learner-guide/en/latest/sfd_dashboard_profile/index.html",
            HelpContextProcessorTest._get_doc_url('profile')
        )

        # Use settings.DOC_LINK_BASE_URL to override default base_url.
        with patch('django.conf.settings.DOC_LINK_BASE_URL', 'settings_base_url'):
            self.assertEqual(
                "settings_base_url/en/latest/SFD_instructor_dash_help.html",
                HelpContextProcessorTest._get_doc_url('instructor')
            )

    def test_get_pdf_url(self):
        # Test default values.
        self.assertEqual(
            "https://media.readthedocs.org/pdf/open-edx-learner-guide/latest/open-edx-learner-guide.pdf",
            HelpContextProcessorTest._get_pdf_url()
        )

        # Use settings.DOC_LINK_BASE_URL to override default base_url.
        with patch('django.conf.settings.DOC_LINK_BASE_URL', 'settings_base_url'):
            self.assertEqual(
                "settings_base_url/latest/open-edx-learner-guide.pdf",
                HelpContextProcessorTest._get_pdf_url()
            )

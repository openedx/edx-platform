"""
Test the Studio help links.
"""

from flaky import flaky

from .base_studio_test import StudioCourseTest
from ...pages.studio.index import DashboardPage
from ...pages.studio.utils import click_studio_help, studio_help_links


class StudioHelpTest(StudioCourseTest):
    """Tests for Studio help."""

    @flaky  # TODO: TNL-4954
    def test_studio_help_links(self):
        """Test that the help links are present and have the correct content."""
        page = DashboardPage(self.browser)
        page.visit()
        click_studio_help(page)
        links = studio_help_links(page)
        expected_links = [{
            'href': u'http://docs.edx.org/',
            'text': u'edX Documentation',
            'sr_text': u'Access documentation on http://docs.edx.org'
        }, {
            'href': u'https://open.edx.org/',
            'text': u'Open edX Portal',
            'sr_text': u'Access the Open edX Portal'
        }, {
            'href': u'https://www.edx.org/course/overview-creating-edx-course-edx-edx101#.VO4eaLPF-n1',
            'text': u'Enroll in edX101',
            'sr_text': u'Enroll in edX101: Overview of Creating an edX Course'
        }, {
            'href': u'https://www.edx.org/course/creating-course-edx-studio-edx-studiox',
            'text': u'Enroll in StudioX',
            'sr_text': u'Enroll in StudioX: Creating a Course with edX Studio'
        }, {
            'href': u'mailto:partner-support@example.com',
            'text': u'Contact Us',
            'sr_text': 'Send an email to partner-support@example.com'
        }]
        for expected, actual in zip(expected_links, links):
            self.assertEqual(expected['href'], actual.get_attribute('href'))
            self.assertEqual(expected['text'], actual.text)
            self.assertEqual(
                expected['sr_text'],
                actual.find_element_by_xpath('following-sibling::span').text
            )

# coding: utf-8
"""
Acceptance tests for Studio's Setting pages
"""


import os
from mock import patch

from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.pages.studio.settings import SettingsPage
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from openedx.core.lib.tests import attr


@attr('a11y')
class StudioSettingsA11yTest(StudioCourseTest):

    """
    Class to test Studio pages accessibility.
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super(StudioSettingsA11yTest, self).setUp()
        self.settings_page = SettingsPage(self.browser, self.course_info['org'], self.course_info['number'],
                                          self.course_info['run'])

    def test_studio_settings_page_a11y(self):
        """
        Check accessibility of SettingsPage.
        """
        self.settings_page.visit()
        self.settings_page.wait_for_page()

        self.settings_page.a11y_audit.config.set_rules({
            "ignore": [
                'link-href',  # TODO: AC-590
                'aria-allowed-role',  # TODO: AC-936
                'landmark-complementary-is-top-level',  # TODO: AC-939
                'radiogroup',  # TODO:  AC-941
                'region',  # TODO: AC-932
            ],
        })

        self.settings_page.a11y_audit.check_for_accessibility_errors()


@attr('a11y')
class StudioSubsectionSettingsA11yTest(StudioCourseTest):
    """
    Class to test accessibility on the subsection settings modals.
    """

    def setUp(self):  # pylint: disable=arguments-differ
        browser = os.environ.get('SELENIUM_BROWSER', 'firefox')

        # This test will fail if run using phantomjs < 2.0, due to an issue with bind()
        # See https://github.com/ariya/phantomjs/issues/10522 for details.

        # The course_outline uses this function, and as such will not fully load when run
        # under phantomjs 1.9.8. So, to prevent this test from timing out at course_outline.visit(),
        # force the use of firefox vs the standard a11y test usage of phantomjs 1.9.8.

        # TODO: remove this block once https://openedx.atlassian.net/browse/TE-1047 is resolved.
        if browser == 'phantomjs':
            browser = 'firefox'

        with patch.dict(os.environ, {'SELENIUM_BROWSER': browser}):
            super(StudioSubsectionSettingsA11yTest, self).setUp(is_staff=True)

        self.course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        course_fixture.add_advanced_settings({
            "enable_proctored_exams": {"value": "true"}
        })

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 1').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1')
                )
            )
        )

    def test_special_exams_menu_a11y(self):
        """
        Given that I am a staff member
        And I am editing settings on the special exams menu
        Then that menu is accessible
        """
        self.course_outline.visit()
        self.course_outline.open_subsection_settings_dialog()
        self.course_outline.select_advanced_tab()

        self.course_outline.a11y_audit.config.set_rules({
            "ignore": [
                'section',  # TODO: AC-491
            ],
        })
        # limit the scope of the audit to the special exams tab on the modal dialog
        self.course_outline.a11y_audit.config.set_scope(
            include=['section.edit-settings-timed-examination']
        )
        self.course_outline.a11y_audit.check_for_accessibility_errors()

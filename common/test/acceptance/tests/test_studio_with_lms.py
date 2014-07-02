# -*- coding: utf-8 -*-

"""
Acceptance tests that uses both Studio and LMS.
"""

from .helpers import UniqueCourseTest
from ..pages.lms.courseware import CoursewarePage
from ..pages.studio.auto_auth import AutoAuthPage
from ..pages.studio.overview import CourseOutlinePage
from ..fixtures.course import CourseFixture, XBlockFixtureDesc


class StudioLMSTest(UniqueCourseTest):
    """ Test Studio Unit in LMS """

    def setUp(self):

        super(StudioLMSTest, self).setUp()

        self.html_content = '<p><strong>Body of HTML Unit.</strong></p>'

        self.courseware = CoursewarePage(self.browser, self.course_id)

        self.outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        # Create course wiht HTML component
        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc("vertical", "Test Unit").add_children(
                        XBlockFixtureDesc('html', 'HTML Unit', data=self.html_content),
                    )
                )
            )
        ).install()

        # Auto login and register the course
        self.auth_page = AutoAuthPage(
            self.browser,
            staff=False,
            username=course_fix.user.get('username'),
            email=course_fix.user.get('email'),
            password=course_fix.user.get('password')
        ).visit()

    def test_studio_unit_in_lms(self):
        """
        Create a course programmatically with an HTML component in a unit.
        Navigate to that unit in Studio, and then click the View Live button to show it in LMS.
        Verify that you see the HTML content in LMS.
        """
        # Visit Course Outline page
        self.outline.visit()

        # Visit Unit page
        unit_page = self.outline.section('Test Section').subsection('Test Subsection').toggle_expand().unit(
            'Test Unit').go_to()

        # Click on View Live button to view the html unit in LMS
        # This will open a new Browser Window
        unit_page.click_view_live_button()

        # Get handles of all browser windows
        # This will return a list
        browser_window_handles = self.browser.window_handles

        # Switch to browser window that shows HTML Unit in LMS
        # The last handle represents the latest windows opened
        self.browser.switch_to_window(browser_window_handles[-1])

        # Now Verify that we are seeing xblock HTML component with correct HTML content

        # First, Verify that rendered xblock component is of type `html`
        self.assertEqual(self.courseware.xblock_component_type, 'html')

        # Second, Verify that HTML content is correct
        self.assertEqual(self.courseware.xblock_component_html_content, self.html_content)

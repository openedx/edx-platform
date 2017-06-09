# -*- coding: utf-8 -*-
"""
End-to-end tests for the CCX dashboard.
"""
from nose.plugins.attrib import attr

from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.tests.helpers import UniqueCourseTest, EventsTestMixin
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.ccx_dashboard_page import CoachDashboardPage


@attr(shard=7)
class CreateCCXCoachTest(EventsTestMixin, UniqueCourseTest):
    """
    Test ccx end to end process.
    """
    USERNAME = "coach_tester"
    EMAIL = "coach_tester@example.com"

    def setUp(self):
        super(CreateCCXCoachTest, self).setUp()
        self.course_info.update({"settings": {"enable_ccx": "true"}})
        self.course_fixture = CourseFixture(**self.course_info)
        self.course_fixture.add_advanced_settings({
            "enable_ccx": {"value": "true"}
        })
        self.course_fixture.install()

        self.auto_auth(self.USERNAME, self.EMAIL)
        self.coach_dashboard_page = self.visit_coach_dashboard()

    def auto_auth(self, username, email):
        """
        Logout and login with given credentials.
        """
        AutoAuthPage(self.browser, username=username, email=email,
                     course_id=self.course_id, staff=True).visit()

    def visit_coach_dashboard(self):
        """
        Visits the instructor dashboard.
        """
        coach_dashboard_page = CoachDashboardPage(self.browser, self.course_id)
        coach_dashboard_page.visit()
        return coach_dashboard_page

    def test_create_ccx(self):
        """
        Assert that ccx created.
        """
        ccx_name = "Test ccx"

        self.coach_dashboard_page.fill_ccx_name_text_box(ccx_name)
        self.coach_dashboard_page.wait_for_page()

        # Assert that new ccx is created and we are on ccx dashboard/enrollment tab.
        self.assertTrue(self.coach_dashboard_page.is_browser_on_enrollment_page())

        # Assert that the user cannot click in the "View Unit in Studio" button,
        # which means the user cannot edit the ccx course in studio
        self.assertFalse(self.coach_dashboard_page.is_button_view_unit_in_studio_visible())

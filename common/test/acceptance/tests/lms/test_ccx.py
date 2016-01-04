# -*- coding: utf-8 -*-
"""
End-to-end tests for the CCX dashboard.
"""
from nose.plugins.attrib import attr

from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.tests.helpers import UniqueCourseTest, EventsTestMixin
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.ccx_dashboard_page import CoachDashboardPage


@attr('shard_7')
class BaseCCXCoachTest(EventsTestMixin, UniqueCourseTest):
    """
    Base methods for CCX dashboard testing.
    """
    USERNAME = "coach_tester"
    EMAIL = "coach_tester@example.com"

    def setUp(self):
        super(BaseCCXCoachTest, self).setUp()
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

    def create_ccx(self):
        """
        create ccx
        """
        ccx_name = "Test ccx"

        self.coach_dashboard_page.fill_ccx_name_text_box(ccx_name)
        self.coach_dashboard_page.wait_for_page()


@attr('shard_7')
class CreateCCXCoachTest(BaseCCXCoachTest):
    """
    Test ccx end to end process.
    """
    def test_create_ccx(self):
        """
        Assert that ccx created.
        """
        self.create_ccx()
        # Assert that new ccx is created and we are on ccx dashboard/enrollment tab.
        self.assertTrue(self.coach_dashboard_page.is_browser_on_enrollment_page())


@attr('a11y')
class ScheduleTabA11yTest(BaseCCXCoachTest):
    """
    Class to test schedule tab accessibility.
    """

    def test_schedule_tab_a11y(self):
        """
        Test schedule tab accessibility.
        """
        self.create_ccx()
        schedule_section = self.coach_dashboard_page.select_schedule()

        schedule_section.a11y_audit.config.set_rules({
            'ignore': [
                'link-href', 'skip-link'  # TODO: AC-233
            ],
        })
        schedule_section.a11y_audit.check_for_accessibility_errors()

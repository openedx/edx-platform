# -*- coding: utf-8 -*-
"""
CCX coach dashboard page
"""
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from common.test.acceptance.pages.lms.course_page import CoursePage


class CoachDashboardPage(CoursePage):
    """
    CCX coach dashboard, where ccx coach can manage a course.
    """
    url_path = "ccx_coach"

    def is_browser_on_page(self):
        """
        check if ccx dashboard is open.
        """
        return self.q(css='div.instructor-dashboard-wrapper-2').present

    def is_browser_on_enrollment_page(self):
        """
        check if enrollment page in ccx dashboard is open.
        """
        return self.q(css='div.batch-enrollment').present

    def select_schedule(self):
        """
        Selects the membership tab and returns the MembershipSection
        """
        self.q(css='a[data-section=schedule]').first.click()
        schedule_section = SchedulePage(self.browser)
        schedule_section.wait_for_page()
        return schedule_section

    def fill_ccx_name_text_box(self, ccx_name):
        """
        Fill in the form with the provided ccx name and submit it.
        """
        ccx_name_selector = "#ccx_name"
        create_ccx_button = "#create-ccx"

        # Fill the ccx_name.
        self.wait_for_element_visibility(ccx_name_selector, 'CCX name field is visible')
        self.q(css=ccx_name_selector).fill(ccx_name)

        # Verify create ccx button is present before clicking.
        EmptyPromise(
            lambda: self.q(css=create_ccx_button).present, "Create a new Custom Course for edX"
        ).fulfill()
        self.q(css=create_ccx_button).click()


class SchedulePage(PageObject):
    """
    CCX schedule page of the coach dashboard.
    """
    url = None

    def is_browser_on_page(self):
        return self.q(css='a[data-section=schedule].active-section').present

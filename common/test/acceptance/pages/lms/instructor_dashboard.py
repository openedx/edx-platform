# -*- coding: utf-8 -*-
"""
Instructor (2) dashboard page.
"""

from bok_choy.page_object import PageObject
from .course_page import CoursePage


class InstructorDashboardPage(CoursePage):
    """
    Instructor dashboard, where course staff can manage a course.
    """
    url_path = "instructor"

    def is_browser_on_page(self):
        return self.q(css='div.instructor-dashboard-wrapper-2').present

    def select_membership(self):
        """
        Selects the membership tab and returns the MembershipSection
        """
        self.q(css='a[data-section=membership]').first.click()
        membership_section = MembershipPage(self.browser)
        membership_section.wait_for_page()
        return membership_section


class MembershipPage(PageObject):
    """
    Membership section of the Instructor dashboard.
    """
    url = None

    def is_browser_on_page(self):
        return self.q(css='a[data-section=membership].active-section').present

    def _get_cohort_options(self):
        """
        Returns the available options in the cohort dropdown, including the initial "Select a cohort".
        """
        return self.q(css=".cohort-management #cohort-select option")

    def _name_without_count(self, name_with_count):
        """
        Returns the name of the cohort with the count information excluded.
        """
        return name_with_count.split(' (')[0]

    def get_cohorts(self):
        """
        Returns, as a list, the names of the available cohorts in the drop-down, filtering out "Select a cohort".
        """
        return [
            self._name_without_count(opt.text)
            for opt in self._get_cohort_options().filter(lambda el: el.get_attribute('value') != "")
        ]

    def get_selected_cohort(self):
        """
        Returns the name of the selected cohort.
        """
        return self._name_without_count(
            self._get_cohort_options().filter(lambda el: el.is_selected()).first.text[0]
        )

    def select_cohort(self, cohort_name):
        """
        Selects the given cohort in the drop-down.
        """
        self.q(css=".cohort-management #cohort-select option").filter(
            lambda el: self._name_without_count(el.text) == cohort_name
        ).first.click()

    def get_cohort_group_setup(self):
        """
        Returns the description of the current cohort
        """
        return self.q(css='.cohort-management-group-setup .setup-value').first.text[0]

    def select_edit_settings(self):
        self.q(css=".action-edit").first.click()

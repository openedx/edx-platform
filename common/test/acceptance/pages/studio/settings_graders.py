"""
Course Grading Settings page.
"""

from common.test.acceptance.pages.studio.settings import SettingsPage
from common.test.acceptance.pages.studio.utils import press_the_notification_button
from common.test.acceptance.pages.common.utils import click_css
from bok_choy.promise import BrokenPromise


class GradingPage(SettingsPage):
    """
    Course Grading Settings page.
    """

    url_path = "settings/grading"
    grade_ranges = '.grades .grade-specific-bar'

    def is_browser_on_page(self):
        return self.q(css='body.grading').present

    def letter_grade(self, selector):
        """
        Returns: first letter of grade range on grading page
        Example: if there are no manually added grades it would
        return Pass, if a grade is added it will return 'A'
        """
        return self.q(css=selector)[0].text

    @property
    def total_number_of_grades(self):
        """
        Gets total number of grades present in the grades bar
        returns: Single number length of grades
        """
        self.wait_for_element_visibility(self.grade_ranges, 'Grades are visible')
        return len(self.q(css=self.grade_ranges))

    def add_new_grade(self):
        """
        Add new grade
        """
        self.q(css='.new-grade-button').click()
        self.save_changes()

    def remove_grade(self):
        """
        Remove an added grade
        """
        # Button displays after hovering on it
        btn_css = '.remove-button'
        self.browser.execute_script("$('{}').focus().click()".format(btn_css))
        self.wait_for_ajax()
        self.save_changes()

    def remove_grades(self, number_of_grades):
        """
        Remove grade ranges from grades bar.
        """
        for _ in range(number_of_grades):
            self.browser.execute_script('document.getElementsByClassName("remove-button")[0].click()')

    def remove_all_grades(self):
        """
        Removes all grades
        """
        while len(self.q(css='.remove-button')) > 0:
            self.remove_grade()

    @property
    def grade_letters(self):
        """
        Get names of grade ranges.
        Returns: A list containing names of the grade ranges.
        """
        return self.q(css='.letter-grade').text

    def click_add_grade(self):
        """
        Clicks to add a grade
        """
        click_css(self, '.new-grade-button', require_notification=False)

    def is_grade_added(self, length):
        """
        Checks to see if grade is added by comparing number of grades after the addition
        Returns: True if grade is added
        Returns: False if grade is not added
        """
        try:
            self.wait_for(
                lambda: len(self.q(css=self.grade_ranges)) == length + 1,
                description="Grades are added",
                timeout=3
            )
            return True
        except BrokenPromise:
            return False

    def add_new_assignment_type(self):
        """
        Add New Assignment type
        """
        self.q(css='.add-grading-data').click()
        self.save_changes()

    def fill_assignment_type_fields(
            self,
            name,
            abbreviation,
            total_grade,
            total_number,
            drop
    ):
        """
        Fills text to Assignment Type fields according to assignment box
        number and text provided

        Arguments:
            name: Assignment Type Name
            abbreviation: Abbreviation
            total_grade: Weight of Total Grade
            total_number: Total Number
            drop: Number of Droppable
        """
        self.q(css='#course-grading-assignment-name').fill(name)
        self.q(css='#course-grading-assignment-shortname').fill(abbreviation)
        self.q(css='#course-grading-assignment-gradeweight').fill(total_grade)
        self.q(
            css='#course-grading-assignment-totalassignments'
        ).fill(total_number)

        self.q(css='#course-grading-assignment-droppable').fill(drop)
        self.save_changes()

    def assignment_name_field_value(self):
        """
        Returns: Assignment type field value
        """
        return self.q(css='#course-grading-assignment-name').attrs('value')

    def delete_assignment_type(self):
        """
        Deletes Assignment type
        """
        self.q(css='.remove-grading-data').first.click()
        self.save_changes()

    def delete_all_assignment_types(self):
        """
        Deletes all assignment types
        """
        while len(self.q(css='.remove-grading-data')) > 0:
            self.delete_assignment_type()

    def save(self):
        """
        Click on save settings button.
        """
        press_the_notification_button(self, "Save")

    def refresh_and_wait_for_load(self):
        """
        Refresh the page and wait for all resources to load.
        """
        self.browser.refresh()
        self.wait_for_page()

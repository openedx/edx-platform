"""
Course Grading Settings page.
"""

from common.test.acceptance.pages.studio.settings import SettingsPage
from common.test.acceptance.pages.studio.utils import press_the_notification_button
from common.test.acceptance.pages.common.utils import click_css
from selenium.webdriver import ActionChains
from bok_choy.promise import BrokenPromise


class GradingPage(SettingsPage):
    """
    Course Grading Settings page.
    """

    url_path = "settings/grading"
    grade_ranges = '.grades .grade-specific-bar'
    assignments = '.field-group.course-grading-assignment-list-item'

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
        Returns:
            int: Single number length of grades
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

    def drag_and_drop_grade(self):
        """
        Drag and drop grade range.
        """
        self.wait_for_element_visibility(self.grade_ranges, "Grades ranges are visible")
        # We have used jquery here to adjust the width of slider to
        # desired range because drag and drop has behaved very inconsistently.
        # This does not updates the text of range on the slider.
        # So as a work around, we have used drag_and_drop without any offset
        self.browser.execute_script('$(".ui-resizable").css("width","10")')
        action = ActionChains(self.browser)
        moveable_css = self.q(css='.ui-resizable-e').results[0]
        action.drag_and_drop_by_offset(moveable_css, 0, 0).perform()

    @property
    def get_assignment_names(self):
        """
        Get name of the all the assignment types.
        Returns:
            list: A list containing names of the assignment types.
        """
        self.wait_for_element_visibility(
            '#course-grading-assignment-name',
            'Grade Names not visible.'
        )
        return self.q(css='#course-grading-assignment-name').attrs('value')

    def change_assignment_name(self, old_name, new_name):
        """
        Changes the assignment name.
        Arguments:
            old_name (str): The assignment type name which is to be changed.
            new_name (str): New name of the assignment.
        """
        self.wait_for_element_visibility('#course-grading-assignment-name', 'Assignment Name field visible')
        self.q(css='#course-grading-assignment-name').filter(
            lambda el: el.get_attribute('value') == old_name).fill(new_name)

    @property
    def grade_letters(self):
        """
        Get names of grade ranges.
        Returns:
            list: A list containing names of the grade ranges.
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
        Returns:
            bool: True if grade is added
            bool: False if grade is not added
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

    @property
    def grades_range(self):
        """
        Get ranges of all the grades.
        Returns:
            list: A list containing ranges of all the grades
        """
        self.wait_for_element_visibility('.range', 'Ranges are visible')
        return self.q(css='.range').text

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
        Returns:
            list: Assignment type field value
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

    def get_confirmation_message(self):
        """
        Get confirmation message received after saving settings.
        """
        self.wait_for_element_visibility('#alert-confirmation-title', 'Confirmation text present')
        return self.q(css='#alert-confirmation-title').text[0]

    def _get_type_index(self, name):
        """
        Gets the index of assignment type.
        Arguments:
            name(str): name of the assignment
        Returns:
            int: index of the assignment type
        """
        name_id = '#course-grading-assignment-name'
        all_types = self.q(css=name_id).results
        for index, element in enumerate(all_types):
            if element.get_attribute('value') == name:
                return index
        return -1

    def save(self):
        """
        Click on save settings button.
        """
        press_the_notification_button(self, "Save")

    def cancel(self):
        """
        Click on cancel settings button.
        """
        press_the_notification_button(self, "Cancel")

    def refresh_and_wait_for_load(self):
        """
        Refresh the page and wait for all resources to load.
        """
        self.browser.refresh()
        self.wait_for_page()

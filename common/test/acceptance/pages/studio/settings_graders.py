"""
Course Grading Settings page.
"""

from common.test.acceptance.pages.studio.course_page import CoursePage
from common.test.acceptance.pages.common.utils import click_css
from common.test.acceptance.pages.studio.utils import press_the_notification_button
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from bok_choy.promise import BrokenPromise
from nose.tools import assert_not_equal


class GradingPage(CoursePage):
    """
    Course Grading Settings page.
    """

    url_path = "settings/grading"
    grace_period_field = '#course-grading-graceperiod'
    grade_ranges = '.grades .grade-specific-bar'

    def is_browser_on_page(self):
        return (self.q(css='body.grading').present and
                self.q(css='.new-grade-button').present)

    def add_new_grade(self):
        """
        Adds a new grade in grade bar.
        """
        click_css(self, '.new-grade-button')

    def get_total_number_of_grades(self):
        """
        Gets total number of grades present in the grades bar
        returns: Single number length of grades
        """
        self.wait_for_element_visibility(self.grade_ranges, 'Grades not visible')
        return len(self.q(css=self.grade_ranges))

    def add_grades(self, grades_to_add):
        """
        Add new grade ranges in grades bar.
        """
        self.wait_for_element_visibility('.grades', 'Grade bar not visible')
        for _ in range(grades_to_add):
            length = len(self.q(css=self.grade_ranges))
            click_css(self, '.new-grade-button', require_notification=False)
            self.wait_for(
                lambda: len(self.q(css=self.grade_ranges)) == length + 1 or
                len(self.q(css=self.grade_ranges)) < 6,
                description="Grades are added"
            )

    def remove_grades(self, number_of_grades):
        """
        Remove grade ranges from grades bar.
        """
        for _ in range(number_of_grades):
            self.browser.execute_script('document.getElementsByClassName("remove-button")[0].click()')

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

    def is_notification_button_disbaled(self):
        """
        Check to see if notification button is disabled.
        Returns: True if button is disabled.
        """
        self.wait_for_element_visibility('.nav-actions>ul', 'Notification bar not visible.')
        return self.q(css='.action-primary.action-save.is-disabled').present

    def get_confirmation_message(self):
        """
        Get confirmation message received after saving settings.
        """
        return self.q(css='#alert-confirmation-title').text[0]

    def refresh_and_wait_for_load(self):
        """
        Refresh the page and wait for all resources to load.
        """
        self.browser.refresh()
        self.wait_for_page()

    def get_grade_alphabets(self):
        """
        Get names of grade ranges.
        Returns: A list containing names of the grade ranges.
        """
        return self.q(css='.letter-grade').text

    def add_new_assignment_type(self):
        """
        Click New Assignment Type button.
        """
        self.q(css='.new-button.new-course-grading-item.add-grading-data').click()

    def drag_and_drop_grade(self):
        """
        Drag and drop grade range.
        """
        self.wait_for_element_visibility(self.grade_ranges, "Grades bar not present")
        action = ActionChains(self.browser)
        moveable_css = self.q(css='.ui-resizable-e').results[0]
        action.drag_and_drop_by_offset(moveable_css, 100, 0).perform()

    def get_grade_ranges(self):
        """
        Get ranges of all the grades.
        Returns: A list containing ranges of all the grades
        """
        return self.q(css='.range').text

    def change_assignment_name(self, old_name, new_name):
        """
        Changes the assignment name.
        :param old_name: The assignment type name which is to be changed.
        :param new_name: New name of the assignment.
        """
        self.q(css='#course-grading-assignment-name').filter(
            lambda el: el.get_attribute('value') == old_name).fill(new_name)

    def get_assignment_weight(self, assignment_index=-1):
        """
        Get the weight of last assignment type.
        """
        self.wait_for_element_visibility(
            '#course-grading-assignment-gradeweight',
            'Weight fields are not present'
            )
        all_weight_elements = self.q(css='#course-grading-assignment-gradeweight').results
        return all_weight_elements[assignment_index].get_attribute('value')

    def edit_grade_name(self, new_grade_name):
        """
        Edit name of the highest grade.
        """
        self.wait_for_element_visibility(self.grade_ranges, 'Grades not visible')
        self.q(css='span[contenteditable="true"]').fill(new_grade_name)

    def get_highest_grade_name(self):
        """
        Get name of the highest grade.
        """
        self.wait_for_element_visibility(self.grade_ranges, 'Grades not visible')
        return self.q(css='span[contenteditable="true"]').first.text[0]

    def get_lowest_grade_name(self):
        """
        Get name of the lowest grade.
        """
        self.wait_for_element_visibility(self.grade_ranges, 'Grades not visible')
        return self.q(css='span[contenteditable="false"]').first.text[0]

    def try_edit_fail_grade(self, field_value):
        """
        Try to edit the name of lowest grade.
        """
        self.wait_for_element_visibility(self.grade_ranges, 'Grades not visible')
        try:
            self.q(css='span[contenteditable="false"]').fill(field_value)
        except BrokenPromise:
            pass

    def set_grace_period_value(self, grace_time_value):
        """
        Set the grace period on deadline.
        """
        self.wait_for_element_visibility(self.grace_period_field, "Grace Period field not present.")
        self.q(css='#course-grading-graceperiod').fill(grace_time_value)

    def get_grace_period_value(self):
        """
        Get the grace period field value.
        """
        self.wait_for(lambda: self.q(css=self.grace_period_field).attrs('value')[0] != '00:00',
                      description="Grace period field not updated")
        return self.q(css='#course-grading-graceperiod').attrs('value')[0]

    def _get_type_index(self, name):
        """
        Gets the index of assignment type.
        """
        name_id = '#course-grading-assignment-name'
        all_types = self.q(css=name_id).results
        for index, element in enumerate(all_types):
            if element.get_attribute('value') == name:
                return index
        return -1

    def delete_assignment_type(self, assignment_name):
        """
        Delete an assignment type
        :param assignment_name: Assignment type which is to be deleted.
        """
        delete_css = '.remove-grading-data'
        index = self._get_type_index(assignment_name)
        f = self.q(css=delete_css).results[index]
        f.click()

    def set_weight(self, assignment_name, weight):
        """
        Set the weight of the assignment type.
        :param assignment_name: Assignment name for which weight is to be changed.
        :param weight: New weight
        """
        weight_id = '#course-grading-assignment-gradeweight'
        index = self._get_type_index(assignment_name)
        f = self.q(css=weight_id).results[index]
        assert_not_equal(index, -1)
        for __ in xrange(len(assignment_name)):
            f.send_keys(Keys.END, Keys.BACK_SPACE)
        f.send_keys(weight)

    def get_assignment_names(self):
        """
        Get name of the all the assignment types.
        Returns: A list containing names of the assignment types.
        """
        self.wait_for_element_visibility(
            '#course-grading-assignment-name',
            'Grade Names not visible.'
        )
        return self.q(css='#course-grading-assignment-name').attrs('value')

"""
Course Grading Settings page.
"""
from selenium.webdriver.common.action_chains import ActionChains
from bok_choy.promise import EmptyPromise

from .course_page import CoursePage
from .utils import set_input_value, press_the_notification_button


class GradingPage(CoursePage):
    """
    Course Grading Settings page.
    """

    url_path = "settings/grading"
    grading_css = '.settings-grading'

    def is_browser_on_page(self):
        """
        Verify that the browser is on the page and it is not still loading.
        """
        return self.q(css='body.grading').present

    @property
    def assignments(self):
        """
        Return list of the assignments for the course.
        """
        css = self.grading_css + ' .course-grading-assignment-list-item'
        return [Assignment(self, self.grading_css, index + 1) for index in xrange(len(self.q(css=css)))]

    @property
    def grace_period(self):
        """
        Returns grace period.
        """
        return self.q(css='#course-grading-graceperiod').first.attrs('value')[0]

    @grace_period.setter
    def grace_period(self, value):
        """
        Sets grace period.
        """
        set_input_value(self, '#course-grading-graceperiod', value)

    @property
    def grading_ranges(self):
        """
        Returns grading ranges.
        """
        return self.q(css='.grade-range .range').text

    @property
    def letter_grades(self):
        """
        Return letters.
        """
        return self.q(css='.letter-grade').text

    def add_grading_range(self):
        """
        Adds a new grading range.
        """
        self.q(css='.grade-range .new-grade-button').first.click()

    def remove_grading_range(self, letter):
        """
        Removes grading range by the letter.
        """
        # First element is not removable, that's why we should subtract 1
        index = self._get_index_of('.letter-grade', letter) - 1
        self.browser.execute_script('document.getElementsByClassName("remove-button")[{index}].click()'.format(
            index=index
        ))

    def change_grading_range_name(self, letter, value):
        """
        Set letter grade name by index.
        """
        index = self._get_index_of('.letter-grade', letter)
        self.q(css='.letter-grade').nth(index).fill(value)

    def move_grading_range_by_offset(self, letter, offset_x=0, offset_y=0):
        """
        Moves grading range by the offset.
        """
        # First element is not removable, that's why we should subtract 1
        index = self._get_index_of('.letter-grade', letter) - 1
        draggable = self.q(css='.grade-range .ui-resizable-e').results[index]
        action = ActionChains(self.browser)
        action.drag_and_drop_by_offset(draggable, offset_x, offset_y).release().perform()
        self.click_save_button()

    def refresh(self):
        """
        Reloads the page.
        """
        self.browser.refresh()
        self.wait_for_page()

    def wait_for_assignmnents(self):
        """
        Ensure the assignments available for use.
        """
        EmptyPromise(
            lambda: self.q(css='.course-grading-assignment-list-item').present,
            'Assignment types are finished rendering'
        ).fulfill()

    def wait_for_letter_grades(self):
        """
        Ensure the grading ranges are available for use.
        """
        EmptyPromise(
            lambda: len(self.letter_grades) > 0,
            'Gradeing ranges are rendered.'
        ).fulfill()

    def wait_for_grace_period(self, value):
        """
        Ensure the grading ranges are available for use.
        """
        EmptyPromise(lambda: self.grace_period == value, 'Grace period is changed.').fulfill()

    def wait_for_confirmation_prompt(self):
        """
        Show confirmation prompt.

        We can't use confirm_prompt because its wait_for_notification
        is flaky when asynchronous operation completed very quickly.
        """
        self.wait_for_element_visibility('.notification', 'Notofication is visible')
        self.wait_for_element_visibility('.notification .action-primary', 'Confirmation button is visible')

    def is_confirmation_message_visible(self):
        """
        Indicates whether confirmation message visible.
        """
        return self.q(css="#alert-confirmation").visible

    def is_save_button_disabled(self):
        """
        Indicates whether save button is disabled.
        """
        return self.q(css="div#page-notification button.action-save.is-disabled").present

    def click_add_assignment_button(self):
        """
        Clicks the 'New Assignment Type' button.
        """
        self.q(css=self.grading_css + " .add-grading-data").first.click()

    def click_save_button(self):
        """
        Saves page changes.
        """
        self.wait_for_confirmation_prompt()
        press_the_notification_button(self, 'Save')

    def click_cancel_button(self):
        """
        Restores page changes.
        """
        self.wait_for_confirmation_prompt()
        press_the_notification_button(self, 'Cancel')

    def get_assignment_by_name(self, name):
        """
        Returns an assignment by the name.
        """
        for assignment in self.assignments:
            if assignment.name == name:
                return assignment
        return None

    def has_assignment_with_name(self, name):
        """
        Indicates whether an assignment with the name exists.
        """
        return True if self.get_assignment_by_name(name) else False

    def _get_index_of(self, css, expected_key):
        """
        Returns an index of the element which contains `expected_key`.
        """
        for i, element in enumerate(self.q(css=css)):  # pylint: disable=unused-variable
            # Sometimes get stale reference if I hold on to the array of elements
            key = self.q(css=css).nth(i).text[0]
            if key == expected_key:
                return i
        return -1


class Assignment(object):
    """
    Assignment page object wrapper.
    """

    def __init__(self, page, prefix, index):
        self.page = page
        self.selector = prefix + ' .course-grading-assignment-list-item:nth-child({index})'.format(index=index)
        self.index = index

    def get_selector(self, css=''):
        """
        Return selector for the assignment type container.
        """
        return ' '.join([self.selector, css])

    def find_css(self, css_selector):
        """
        Find elements as defined by css locator.
        """
        return self.page.q(css=self.get_selector(css=css_selector))

    @property
    def name(self):
        """
        Return assignment name.
        """
        return self.find_css('#course-grading-assignment-name').first.attrs('value')[0]

    @name.setter
    def name(self, value):
        """
        Set assignment name.
        """
        set_input_value(self.page, self.get_selector(css='#course-grading-assignment-name'), value)

    @property
    def weight(self):
        """
        Return assignment weight.
        """
        return int(self.find_css('#course-grading-assignment-gradeweight').first.attrs('value')[0])

    @weight.setter
    def weight(self, value):
        """
        Set assignment weight.
        """
        set_input_value(self.page, self.get_selector(css='#course-grading-assignment-gradeweight'), value)

    @property
    def passing_grade(self):
        """
        Return assignment passing grade.
        """
        return int(self.find_css('#assignment-passing-grade').first.attrs('value')[0])

    @passing_grade.setter
    def passing_grade(self, value):
        """
        Set assignment passing grade.
        """
        set_input_value(self.page, self.get_selector(css='#assignment-passing-grade'), value)

    def delete(self):
        """
        Delete the assignment type.
        """
        self.find_css('.remove-grading-data').first.click()

    def click_enable_passing_grade(self):
        """
        Clicks the 'Passing Grade Enabled' checkbox.
        """
        self.page.q(css=self.selector+' #assignment-passing-grade-enabled').click()

    def __repr__(self):
        return "<{}:{}>".format(self.__class__.__name__, self.name)

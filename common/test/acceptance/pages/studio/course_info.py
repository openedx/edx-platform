"""
Course Updates page.
"""
from common.test.acceptance.pages.common.utils import click_css, confirm_prompt
from common.test.acceptance.pages.studio.course_page import CoursePage
from common.test.acceptance.pages.studio.utils import type_in_codemirror, set_input_value


class CourseUpdatesPage(CoursePage):
    """
    Course Updates page.
    """
    url_path = "course_info"

    def is_browser_on_page(self):
        """
        Returns whether or not the browser on the page and has loaded the required content
        """
        # Check for the presence of handouts-content, when it is present the render function has completed
        # loading the updates and handout sections
        return (self.q(css='.handouts-content').present and
                self.q(css='article#course-update-view.course-updates').present)

    def is_course_update_list_empty(self):
        """
        Checks whether or not the update contents list is empty
        """
        return len(self.q(css='.update-contents')) == 0

    def is_new_update_button_present(self):
        """
        Checks for the presence of the new update post button.
        """
        return self.q(css='.new-update-button').present

    def click_new_update_button(self):
        """
        Clicks the new-update button.
        """
        click_css(self, '.new-update-button', require_notification=False)

    def submit_update(self, message):
        """
        Adds update text to the new update CodeMirror form and submits that text.

        Arguments:
            message (str): The message to be added and saved.
        """
        type_in_codemirror(self, 0, message)
        self.click_new_update_save_button()

    def set_date(self, date):
        """
        Sets the updates date input to the provided value.

        Arguments:
            date (str): Date string in the format DD/MM/YYYY
        """
        set_input_value(self, 'input.date', date)

    def is_first_update_date(self, search_date):
        """
        Checks to see if the search date is present

        Arguments:
            search_date (str): e.g. 06/01/2013 would be found with June 1, 2013

        Returns:
             bool: True if the date is in the first update and False otherwise.
        """
        return search_date == self.q(css='.date-display').html[0]

    def is_new_update_save_button_present(self):
        """
        Checks to see if the CodeMirror Update save button is present.
        """
        return self.q(css='.save-button').present

    def click_new_update_save_button(self):
        """
        Clicks the CodeMirror Update save button.
        """
        click_css(self, '.save-button')

    def is_edit_button_present(self):
        """
        Checks to see if the edit update post buttons if present.
        """
        return self.q(css='.post-preview .edit-button').present

    def click_edit_update_button(self):
        """
        Clicks the edit update post button.
        """
        click_css(self, '.post-preview .edit-button', require_notification=False)
        self.wait_for_element_visibility('.CodeMirror', 'Waiting for .CodeMirror')

    def is_delete_update_button_present(self):
        """
        Checks to see if the delete update post button is present.
        """
        return self.q(css='.post-preview .delete-button').present

    def click_delete_update_button(self):
        """
        Clicks the delete update post button and confirms the delete notification.
        """
        click_css(self, '.post-preview .delete-button', require_notification=False)
        confirm_prompt(self)

    def is_first_update_message(self, message):
        """
        Looks for the message in the first course update posted.

        Arguments:
            message (str): String containing the message that is to be searched for

        Returns:
            bool: True if the first update is the message, false otherwise.
        """
        return message == self.q(css='.update-contents').html[0]

    def first_update_contains_html(self, value):
        """
        Looks to see if the html provided is contained in the first update

        Arguments:
            value (str): String value that will be looked for

        Returns:
            bool: True if the value is contained in the first update
        """
        update = self.q(css='.update-contents').html
        return value in update[0]

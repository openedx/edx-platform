"""
Course Textbooks page.
"""

import requests
from path import path
from .course_page import CoursePage
from bok_choy.promise import EmptyPromise


class TextbooksPage(CoursePage):
    """
    Course Textbooks page.
    """

    url_path = "textbooks"

    def is_browser_on_page(self):
        return self.q(css='body.view-textbooks').present

    def open_add_textbook_form(self):
        """
        open new textbook form by cliking on new textbook button
        """
        self.q(css='.nav-item .new-button').click()

    def get_element_text(self, selector):
        """
        return the text of the css selector
        """
        return self.q(css=selector)[0].text

    def _is_element_visible(self, selector):
        """
        check that the element given in css selector is visible
        """
        query = self.q(css=selector)
        return query.present and query.visible

    def set_input_field_value(self, selector, value):
        """
        set the value of input field by selector
        """
        self.q(css=selector)[0].send_keys(value)

    def upload_pdf_file(self, file_name):
        """
        Uploads a pdf textbook
        """
        # If the pdf upload section has not yet been toggled on, click on the upload pdf button
        test_dir = path(__file__).abspath().dirname().dirname().dirname()
        file_path = test_dir + '/data/uploads/' + file_name

        pdf_upload_toggle = self.q(css=".edit-textbook .action-upload").first
        if pdf_upload_toggle:
            pdf_upload_toggle.click()
        file_input = self.q(css=".upload-dialog input").results[0]
        file_input.send_keys(file_path)
        self.q(css=".wrapper-modal-window-assetupload .action-upload").first.click()
        EmptyPromise(
            lambda: not self._is_element_visible(".wrapper-modal-window-assetupload"),
            "Upload modal closed"
        ).fulfill()

    def click_textbook_submit_button(self, textbook_name):
        """
        submit the new textbook form and check if it is rendered properly
        """
        self.q(css='#edit_textbook_form button[type="submit"]').first.click()
        EmptyPromise(
            lambda: textbook_name == self.q(css='.textbook .textbook-title').text[0],
            "Textbook uploaded"
        )

    def is_view_live_link_worked(self):
        """
        check if the view live button of textbook is working fine
        """
        url = self.q(css='.textbook .action-view a').attrs('href')[0]
        try:
            response = requests.get(url)
        except requests.exceptions.ConnectionError:
            return False

        if response.status_code == 200:
            return True

        return False

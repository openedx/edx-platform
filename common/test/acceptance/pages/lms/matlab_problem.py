"""
Matlab Problem Page.
"""
from bok_choy.page_object import PageObject


class MatlabProblemPage(PageObject):
    """
    View of matlab problem page.
    """

    url = None

    def is_browser_on_page(self):
        return self.q(css='.ungraded-matlab-result').present

    @property
    def problem_name(self):
        """
        Return the current problem name.
        """
        return self.q(css='.problem-header').text[0]

    def set_response(self, response_str):
        """
        Input a response to the prompt.
        """
        input_css = "$('.CodeMirror')[0].CodeMirror.setValue('{}');".format(response_str)
        self.browser.execute_script(input_css)

    def click_run_code(self):
        """
        Click the run code button.
        """
        self.q(css='input.save').click()
        self.wait_for_ajax()

    def get_grader_msg(self, class_name):
        """
        Returns the text value of given class.
        """
        self.wait_for_element_visibility(class_name, 'Grader message is visible')
        return self.q(css=class_name).text

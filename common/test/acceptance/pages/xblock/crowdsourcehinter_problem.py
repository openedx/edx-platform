"""
PageObject for Crowdsourcehinter
"""
from bok_choy.page_object import PageObject


class CrowdsourcehinterProblemPage(PageObject):
    """
    A PageObject representing the Crowdsourcehinter xblock.
    """

    url = None

    def __init__(self, browser):
        """
        Args:
            browser (selenium.webdriver): The Selenium-controlled browser that this page is loaded in.
        """
        super(CrowdsourcehinterProblemPage, self).__init__(browser)

    def is_browser_on_page(self):
        return len(self.browser.find_elements_by_class_name('crowdsourcehinter_block')) > 0

    def submit_text_answer(self, text):
        """
        Submit an answer to the problem block
        """
        self.q(css='input[type="text"]').fill(text)
        self.q(css='.action [data-value="Submit"]').click()
        self.wait_for_ajax()

    def get_hint_text(self):
        """
        Return the hint shown to the student
        """
        return self.q(css='div.csh_hint_text').text

    def get_student_answer_text(self):
        """
        Check the student answer is set correctly
        """
        return self.q(css='div.csh_hint_text').attrs('student_answer')

    def rate_hint(self):
        """
        Click the rate_hint button
        """
        self.q(css='div.csh_rate_hint').click()
        self.wait_for_ajax()

    def submit_new_hint(self, text):
        """
        Fill in the textbox and submit a new hint
        """
        self.q(css='.csh_student_hint_creation input[type="button"]').click()
        self.wait_for_ajax()
        self.q(css='.csh_student_text_input input[type="text"]').fill(text)
        self.q(css='.csh_submit_new input[type="button"]').click()
        self.wait_for_ajax()

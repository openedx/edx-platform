"""
Problem Page.
"""


from bok_choy.page_object import PageObject

from common.test.acceptance.pages.common.utils import click_css


class ProblemPage(PageObject):
    """
    View of problem page.
    """

    url = None
    CSS_PROBLEM_HEADER = '.problem-header'
    status_indicators = {
        'correct': ['span.correct'],
        'incorrect': ['span.incorrect'],
        'unanswered': ['span.unanswered'],
        'submitted': ['span.submitted'],
        'unsubmitted': ['.unsubmitted']
    }

    def is_browser_on_page(self):
        return self.q(css='.xblock-student_view').present

    @property
    def problem_name(self):
        """
        Return the current problem name.
        """
        self.wait_for_element_visibility(self.CSS_PROBLEM_HEADER, 'wait for problem header')
        return self.q(css='.problem-header').text[0]

    def click_submit(self):
        """
        Click the Submit button.
        """
        click_css(self, '.problem .submit')

    def click_choice(self, choice_value):
        """
        Click the choice input(radio, checkbox or option) where value matches `choice_value` in choice group.
        """
        self.q(css='div.problem .choicegroup input[value="' + choice_value + '"]').first.click()
        self.wait_for_ajax()

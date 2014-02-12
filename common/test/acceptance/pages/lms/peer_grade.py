"""
Students grade peer submissions.
"""

from bok_choy.page_object import PageObject
from .rubric import RubricPage


class PeerGradePage(PageObject):
    """
    Students grade peer submissions.
    """

    url = None

    def is_browser_on_page(self):
        return (
            self.is_css_present('div.peer-grading-tools') or
            self.is_css_present('div.grading-panel.current-state')
        )

    @property
    def problem_list(self):
        """
        Return the list of available problems to peer grade.
        """
        return self.css_text('a.problem-button')

    def select_problem(self, problem_name):
        """
        Choose the problem with `problem_name` to start grading or calibrating.
        """
        index = self.problem_list.index(problem_name) + 1
        self.css_click('a.problem-button:nth-of-type({})'.format(index))

    @property
    def rubric(self):
        """
        Return a `RubricPage` to allow students to grade their peers.
        If no rubric is available, raises a `BrokenPromise` exception.
        """
        rubric = RubricPage(self.browser)
        rubric.wait_for_page()
        return rubric

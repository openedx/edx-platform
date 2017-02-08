"""
Students grade peer submissions.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import Promise


class PeerGradePage(PageObject):
    """
    Students grade peer submissions.
    """

    url = None

    def is_browser_on_page(self):
        def _is_correct_page():
            is_present = (
                self.q(css='div.peer-grading-tools').present or
                self.q(css='div.grading-panel.current-state').present
            )
            return is_present, is_present

        return Promise(_is_correct_page, 'On the peer grading page.').fulfill()

    @property
    def problem_list(self):
        """
        Return the list of available problems to peer grade.
        """
        return self.q(css='a.problem-button').text

    def select_problem(self, problem_name):
        """
        Choose the problem with `problem_name` to start grading or calibrating.
        """
        index = self.problem_list.index(problem_name) + 1
        self.q(css='a.problem-button:nth-of-type({})'.format(index)).first.click()

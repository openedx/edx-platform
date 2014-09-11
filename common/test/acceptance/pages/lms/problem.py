"""
Problem Page.
"""
from bok_choy.page_object import PageObject


class ProblemPage(PageObject):
    """
    View of problem page.
    """

    url = None

    def is_browser_on_page(self):
        return self.q(css='.xblock-student_view').present

    @property
    def problem_name(self):
        """
        Return the current problem name.
        """
        return self.q(css='.problem-header').text[0]

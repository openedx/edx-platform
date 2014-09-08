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

    @property
    def problem_text(self):
        """
        Return the text of the question of the problem.
        """
        return self.q(css="div.problem p").text

    def fill_answer(self, text):
        """
        Fill in the answer to the problem.
        """
        self.q(css='div.problem div.capa_inputtype.textline input').fill(text)

    def click_check(self):
        """
        Click the Check button!
        """
        self.q(css='div.problem input.check').click()
        self.wait_for_ajax()

    def is_correct(self):
        """
        Is there a "correct" status showing?
        """
        return self.q(css="div.problem div.capa_inputtype.textline div.correct p.status").is_present()



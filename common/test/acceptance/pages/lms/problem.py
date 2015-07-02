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

    @property
    def message_text(self):
        """
        Return the "message" text of the question of the problem.
        """
        return self.q(css="div.problem span.message").text[0]

    @property
    def hint_text(self):
        """
        Return the "hint" text of the problem from its div.
        """
        return self.q(css="div.problem div.problem-hint").text[0]

    def fill_answer(self, text):
        """
        Fill in the answer to the problem.
        """
        self.q(css='div.problem div.capa_inputtype.textline input').fill(text)

    def click_check(self):
        """
        Click the Check button!
        """
        self.q(css='div.problem button.check').click()
        self.wait_for_ajax()

    def click_hint(self):
        """
        Click the Hint button.
        """
        self.q(css='div.problem button.hint-button').click()
        self.wait_for_ajax()

    def is_correct(self):
        """
        Is there a "correct" status showing?
        """
        return self.q(css="div.problem div.capa_inputtype.textline div.correct span.status").is_present()

    def click_clarification(self, index=0):
        """
        Click on an inline icon that can be included in problem text using an HTML <clarification> element:

        Problem <clarification>clarification text hidden by an icon in rendering</clarification> Text
        """
        self.q(css='div.problem .clarification:nth-child({index}) i[data-tooltip]'.format(index=index + 1)).click()

    @property
    def visible_tooltip_text(self):
        """
        Get the text seen in any tooltip currently visible on the page.
        """
        self.wait_for_element_visibility('body > .tooltip', 'A tooltip is visible.')
        return self.q(css='body > .tooltip').text[0]

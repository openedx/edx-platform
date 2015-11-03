"""
Problem Page.
"""
from bok_choy.page_object import PageObject


class ProblemPage(PageObject):
    """
    View of problem page.
    """

    url = None
    CSS_PROBLEM_HEADER = '.problem-header'

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

    def verify_mathjax_rendered_in_problem(self):
        """
        Check that MathJax have been rendered in problem hint
        """
        def mathjax_present():
            """ Returns True if MathJax css is present in the problem body """
            mathjax_container = self.q(css="div.problem p .MathJax .math")
            return mathjax_container.visible and mathjax_container.present

        self.wait_for(
            mathjax_present,
            description="MathJax rendered in problem body"
        )

    def verify_mathjax_rendered_in_hint(self):
        """
        Check that MathJax have been rendered in problem hint
        """
        def mathjax_present():
            """ Returns True if MathJax css is present in the problem body """
            mathjax_container = self.q(css="div.problem div.problem-hint .MathJax .math")
            return mathjax_container.visible and mathjax_container.present

        self.wait_for(
            mathjax_present,
            description="MathJax rendered in hint"
        )

    def fill_answer(self, text):
        """
        Fill in the answer to the problem.
        """
        self.q(css='div.problem div.capa_inputtype.textline input').fill(text)

    def fill_answer_numerical(self, text):
        """
        Fill in the answer to a numerical problem.
        """
        self.q(css='div.problem section.inputtype input').fill(text)
        self.wait_for_ajax()

    def click_check(self):
        """
        Click the Check button!
        """
        self.q(css='div.problem button.check').click()
        self.wait_for_ajax()

    def wait_for_status_icon(self):
        """
        wait for status icon
        """
        self.wait_for_element_visibility('div.problem section.inputtype div .status', 'wait for status icon')

    def click_hint(self):
        """
        Click the Hint button.
        """
        self.q(css='div.problem button.hint-button').click()
        self.wait_for_ajax()

    def click_choice(self, choice_value):
        """
        Click the choice input(radio, checkbox or option) where value matches `choice_value` in choice group.
        """
        self.q(css='div.problem .choicegroup input[value="' + choice_value + '"]').click()
        self.wait_for_ajax()

    def is_correct(self):
        """
        Is there a "correct" status showing?
        """
        return self.q(css="div.problem div.capa_inputtype.textline div.correct span.status").is_present()

    def simpleprob_is_correct(self):
        """
        Is there a "correct" status showing? Works with simple problem types.
        """
        return self.q(css="div.problem section.inputtype div.correct span.status").is_present()

    def simpleprob_is_partially_correct(self):
        """
        Is there a "partially correct" status showing? Works with simple problem types.
        """
        return self.q(css="div.problem section.inputtype div.partially-correct span.status").is_present()

    def simpleprob_is_incorrect(self):
        """
        Is there an "incorrect" status showing? Works with simple problem types.
        """
        return self.q(css="div.problem section.inputtype div.incorrect span.status").is_present()

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

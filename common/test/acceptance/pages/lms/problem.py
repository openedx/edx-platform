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

    # There can be multiple questions in a problem, so we need to make query selector specific to question
    question_id = 0

    def is_browser_on_page(self):
        return self.q(css='.xblock-student_view').present

    def construct_query_selector(self, selector):
        """
        Construct query selector specific to a question.

        Arguments:
            selector (str): css selector.

        Returns:
            str: Element selector specific to a question.
        """
        return 'div.problem #question-{}.question {}'.format(self.question_id, selector)

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
        return self.q(css=self.construct_query_selector("p")).text

    @property
    def problem_content(self):
        """
        Return the content of the problem
        """
        return self.q(css="div.problems-wrapper").text[0]

    @property
    def message_text(self):
        """
        Return the "message" text of the question of the problem.
        """
        return self.q(css=self.construct_query_selector("span.message")).text[0]

    @property
    def extract_hint_text_from_html(self):
        """
        Return the "hint" text of the problem from html
        """
        return self.q(css=self.construct_query_selector("div.problem-hint")).html[0].split(' <', 1)[0]

    @property
    def hint_text(self):
        """
        Return the "hint" text of the problem from its div.
        """
        return self.q(css=self.construct_query_selector("div.problem-hint")).text[0]

    def verify_mathjax_rendered_in_problem(self):
        """
        Check that MathJax have been rendered in problem hint
        """
        def mathjax_present():
            """ Returns True if MathJax css is present in the problem body """
            mathjax_container = self.q(css=self.construct_query_selector("p .MathJax_SVG"))
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
            mathjax_container = self.q(css=self.construct_query_selector("div.problem-hint .MathJax_SVG"))
            return mathjax_container.visible and mathjax_container.present

        self.wait_for(
            mathjax_present,
            description="MathJax rendered in hint"
        )

    def fill_answer(self, text, input_num=None):
        """
        Fill in the answer to the problem.

        args:
            text: String to fill the input with.

        kwargs:
            input_num: If provided, fills only the input_numth field. Else, all
                input fields will be filled.
        """
        fields = self.q(css=self.construct_query_selector('div.capa_inputtype.textline input'))
        fields = fields.nth(input_num) if input_num is not None else fields
        fields.fill(text)

    def fill_answer_numerical(self, text):
        """
        Fill in the answer to a numerical problem.
        """
        self.q(css=self.construct_query_selector('section.inputtype input')).fill(text)
        self.wait_for_element_invisibility('.loading', 'wait for loading icon to disappear')
        self.wait_for_ajax()

    def click_check(self):
        """
        Click the Check button.
        """
        self.q(css='div.problem button.check').click()
        self.wait_for_ajax()

    def click_save(self):
        """
        Click the Save button.
        """
        self.q(css='div.problem button.save').click()
        self.wait_for_ajax()

    def click_reset(self):
        """
        Click the Reset button.
        """
        self.q(css='div.problem button.reset').click()
        self.wait_for_ajax()

    def wait_for_status_icon(self):
        """
        wait for status icon
        """
        self.wait_for_element_visibility('div.problem section.inputtype div .status', 'wait for status icon')

    def wait_for_expected_status(self, status_selector, message):
        """
        Waits for the expected status indicator.

        Args:
            status_selector(str): status selector string.
            message(str): description of promise, to be logged.
        """
        msg = "Wait for status to be {}".format(message)
        self.wait_for_element_visibility(status_selector, msg)

    def click_hint(self):
        """
        Click the Hint button.
        """
        self.q(css=self.construct_query_selector('button.hint-button')).click()
        self.wait_for_ajax()

    def click_choice(self, choice_value):
        """
        Click the choice input(radio, checkbox or option) where value matches `choice_value` in choice group.
        """
        self.q(css=self.construct_query_selector('.choicegroup input[value="' + choice_value + '"]')).click()
        self.wait_for_ajax()

    def is_correct(self):
        """
        Is there a "correct" status showing?
        """
        return self.q(
            css=self.construct_query_selector("div.capa_inputtype.textline div.correct span.status")
        ).is_present()

    def simpleprob_is_correct(self):
        """
        Is there a "correct" status showing? Works with simple problem types.
        """
        return self.q(
            css=self.construct_query_selector("section.inputtype div.correct span.status")
        ).is_present()

    def simpleprob_is_partially_correct(self):
        """
        Is there a "partially correct" status showing? Works with simple problem types.
        """
        return self.q(
            css=self.construct_query_selector("section.inputtype div.partially-correct span.status")
        ).is_present()

    def simpleprob_is_incorrect(self):
        """
        Is there an "incorrect" status showing? Works with simple problem types.
        """
        return self.q(
            css=self.construct_query_selector("section.inputtype div.incorrect span.status")
        ).is_present()

    def click_clarification(self, index=0):
        """
        Click on an inline icon that can be included in problem text using an HTML <clarification> element:

        Problem <clarification>clarification text hidden by an icon in rendering</clarification> Text
        """
        self.q(css=self.construct_query_selector(
            '.clarification:nth-child({index}) i[data-tooltip]'.format(index=index + 1)
        )).click()

    @property
    def visible_tooltip_text(self):
        """
        Get the text seen in any tooltip currently visible on the page.
        """
        self.wait_for_element_visibility('body > .tooltip', 'A tooltip is visible.')
        return self.q(css='body > .tooltip').text[0]

"""
Problem Page.
"""
from bok_choy.page_object import PageObject
from common.test.acceptance.pages.common.utils import click_css
from selenium.webdriver.common.keys import Keys


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
        self.wait_for_element_visibility(self.CSS_PROBLEM_HEADER, 'wait for problem header')
        return self.q(css='.problem-header').text[0]

    @property
    def problem_text(self):
        """
        Return the text of the question of the problem.
        """
        return self.q(css="div.problem p").text

    @property
    def problem_input_content(self):
        """
        Return the text of the question of the problem.
        """
        return self.q(css="div.wrapper-problem-response").text[0]

    @property
    def problem_content(self):
        """
        Return the content of the problem
        """
        return self.q(css="div.problems-wrapper").text[0]

    @property
    def problem_meta(self):
        """
        Return the problem meta text
        """
        return self.q(css=".problems-wrapper .problem-progress").text[0]

    @property
    def message_text(self):
        """
        Return the "message" text of the question of the problem.
        """
        return self.q(css="div.problem span.message").text[0]

    @property
    def extract_hint_text_from_html(self):
        """
        Return the "hint" text of the problem from html
        """
        hints_html = self.q(css="div.problem .notification-hint .notification-message li").html
        return [hint_html.split(' <span', 1)[0] for hint_html in hints_html]

    @property
    def hint_text(self):
        """
        Return the "hint" text of the problem from its div.
        """
        return self.q(css="div.problem .notification-hint .notification-message").text[0]

    def verify_mathjax_rendered_in_problem(self):
        """
        Check that MathJax have been rendered in problem hint
        """
        def mathjax_present():
            """ Returns True if MathJax css is present in the problem body """
            mathjax_container = self.q(css="div.problem p .MathJax_SVG")
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
            mathjax_container = self.q(css="div.problem div.problem-hint .MathJax_SVG")
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
        fields = self.q(css='div.problem div.capa_inputtype.textline input')
        fields = fields.nth(input_num) if input_num is not None else fields
        fields.fill(text)

    def fill_answer_numerical(self, text):
        """
        Fill in the answer to a numerical problem.
        """
        self.q(css='div.problem div.inputtype input').fill(text)
        self.wait_for_element_invisibility('.loading', 'wait for loading icon to disappear')
        self.wait_for_ajax()

    def click_submit(self):
        """
        Click the Submit button.
        """
        click_css(self, '.problem .submit', require_notification=False)

    def click_save(self):
        """
        Click the Save button.
        """
        click_css(self, '.problem .save', require_notification=False)

    def click_reset(self):
        """
        Click the Reset button.
        """
        click_css(self, '.problem .reset', require_notification=False)

    def click_show(self):
        """
        Click the Show Answer button.
        """
        self.q(css='.problem .show').click()
        self.wait_for_ajax()

    def is_hint_notification_visible(self):
        """
        Is the Hint Notification visible?
        """
        return self.q(css='.notification.notification-hint').visible

    def is_feedback_message_notification_visible(self):
        """
        Is the Feedback Messaged notification visible
        """
        return self.q(css='.wrapper-problem-response .message').visible

    def is_save_notification_visible(self):
        """
        Is the Save Notification Visible?
        """
        return self.q(css='.notification.warning.notification-save').visible

    def is_success_notification_visible(self):
        """
        Is the Submit Notification Visible?
        """
        return self.q(css='.notification.success.notification-submit').visible

    def wait_for_feedback_message_visibility(self):
        """
        Wait for the Feedback Message notification to be visible.
        """
        self.wait_for_element_visibility('.wrapper-problem-response .message',
                                         'Waiting for the Feedback message to be visible')

    def wait_for_save_notification(self):
        """
        Wait for the Save Notification to be present
        """
        self.wait_for_element_visibility('.notification.warning.notification-save',
                                         'Waiting for Save notification to be visible')
        self.wait_for(lambda: self.q(css='.notification.warning.notification-save').focused,
                      'Waiting for the focus to be on the save notification')

    def wait_for_gentle_alert_notification(self):
        """
        Wait for the Gentle Alert Notification to be present
        """
        self.wait_for_element_visibility('.notification.warning.notification-gentle-alert',
                                         'Waiting for Gentle Alert notification to be visible')
        self.wait_for(lambda: self.q(css='.notification.warning.notification-gentle-alert').focused,
                      'Waiting for the focus to be on the gentle alert notification')

    def is_gentle_alert_notification_visible(self):
        """
        Is the Gentle Alert Notification visible?
        """
        return self.q(css='.notification.warning.notification-gentle-alert').visible

    def is_reset_button_present(self):
        """ Check for the presence of the reset button. """
        return self.q(css='.problem .reset').present

    def is_save_button_enabled(self):
        """ Is the Save button enabled """
        return self.q(css='.action .save').attrs('disabled') == [None]

    def is_focus_on_problem_meta(self):
        """
        Check for focus problem meta.
        """
        return self.q(css='.problem-header').focused

    def wait_for_focus_on_problem_meta(self):
        """
        Waits for focus on Problem Meta section
        """
        self.wait_for(
            promise_check_func=self.is_focus_on_problem_meta,
            description='Waiting for focus on Problem Meta section'
        )

    def is_submit_disabled(self):
        """
        Checks if the submit button is disabled
        """
        disabled_attr = self.q(css='.problem .submit').attrs('disabled')[0]
        return disabled_attr == 'true'

    def wait_for_submit_disabled(self):
        """
        Waits until the Submit button becomes disabled.
        """
        self.wait_for(self.is_submit_disabled, 'Waiting for submit to be enabled')

    def wait_for_focus_on_submit_notification(self):
        """
        Check for focus submit notification.
        """

        def focus_check():
            """
            Checks whether or not the focus is on the notification-submit
            """
            return self.q(css='.notification-submit').focused

        self.wait_for(promise_check_func=focus_check, description='Waiting for the notification-submit to gain focus')

    def wait_for_status_icon(self):
        """
        wait for status icon
        """
        self.wait_for_element_visibility('div.problem div.inputtype div .status', 'wait for status icon')

    def wait_for_expected_status(self, status_selector, message):
        """
        Waits for the expected status indicator.

        Args:
            status_selector(str): status selector string.
            message(str): description of promise, to be logged.
        """
        msg = "Wait for status to be {}".format(message)
        self.wait_for_element_visibility(status_selector, msg)

    def is_expected_status_visible(self, status_selector):
        """
        check for the expected status indicator to be visible.

        Args:
            status_selector(str): status selector string.
        """
        return self.q(css=status_selector).visible

    def wait_success_notification(self):
        """
        Check for visibility of the success notification and icon.
        """
        msg = "Wait for success notification to be visible"
        self.wait_for_element_visibility('.notification.success.notification-submit', msg)
        self.wait_for_element_visibility('.fa-check', "Waiting for success icon")
        self.wait_for_focus_on_submit_notification()

    def wait_incorrect_notification(self):
        """
        Check for visibility of the incorrect notification and icon.
        """
        msg = "Wait for error notification to be visible"
        self.wait_for_element_visibility('.notification.error.notification-submit', msg)
        self.wait_for_element_visibility('.fa-close', "Waiting for incorrect notification icon")
        self.wait_for_focus_on_submit_notification()

    def wait_partial_notification(self):
        """
        Check for visibility of the partially visible notification and icon.
        """
        msg = "Wait for partial correct notification to be visible"
        self.wait_for_element_visibility('.notification.success.notification-submit', msg)
        self.wait_for_element_visibility('.fa-asterisk', "Waiting for asterisk notification icon")
        self.wait_for_focus_on_submit_notification()

    def click_hint(self):
        """
        Click the Hint button.
        """
        click_css(self, '.problem .hint-button', require_notification=False)
        self.wait_for_focus_on_hint_notification()

    def wait_for_focus_on_hint_notification(self):
        """
        Wait for focus to be on the hint notification.
        """
        self.wait_for(
            lambda: self.q(css='.notification-hint').focused,
            'Waiting for the focus to be on the hint notification'
        )

    def click_review_in_notification(self, notification_type):
        """
        Click on the "Review" button within the visible notification.
        """
        css_string = '.notification.notification-{notification_type} .review-btn'.format(
            notification_type=notification_type
        )

        # The review button cannot be clicked on until it is tabbed to, so first tab to it.
        # Multiple tabs may be required depending on the content (for instance, hints with links).
        def tab_until_review_focused():
            """ Tab until the review button is focused """
            self.browser.switch_to_active_element().send_keys(Keys.TAB)
            if self.q(css=css_string).focused:
                self.scroll_to_element(css_string)
            return self.q(css=css_string).focused

        self.wait_for(
            tab_until_review_focused,
            'Waiting for the Review button to become focused'
        )
        self.wait_for_element_visibility(
            css_string,
            'Waiting for the button to be visible'
        )
        click_css(self, css_string, require_notification=False)

    def get_hint_button_disabled_attr(self):
        """ Return the disabled attribute of all hint buttons (once hints are visible, there will be two). """
        return self.q(css='.problem .hint-button').attrs('disabled')

    def click_choice(self, choice_value):
        """
        Click the choice input(radio, checkbox or option) where value matches `choice_value` in choice group.
        """
        self.q(css='div.problem .choicegroup input[value="' + choice_value + '"]').first.click()
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
        return self.q(css="div.problem div.inputtype div.correct span.status").is_present()

    def simpleprob_is_partially_correct(self):
        """
        Is there a "partially correct" status showing? Works with simple problem types.
        """
        return self.q(css="div.problem div.inputtype div.partially-correct span.status").is_present()

    def simpleprob_is_incorrect(self):
        """
        Is there an "incorrect" status showing? Works with simple problem types.
        """
        return self.q(css="div.problem div.inputtype div.incorrect span.status").is_present()

    def click_clarification(self, index=0):
        """
        Click on an inline icon that can be included in problem text using an HTML <clarification> element:

        Problem <clarification>clarification text hidden by an icon in rendering</clarification> Text
        """
        self.q(css='div.problem .clarification:nth-child({index}) span[data-tooltip]'.format(index=index + 1)).click()

    @property
    def visible_tooltip_text(self):
        """
        Get the text seen in any tooltip currently visible on the page.
        """
        self.wait_for_element_visibility('body > .tooltip', 'A tooltip is visible.')
        return self.q(css='body > .tooltip').text[0]

    def is_solution_tag_present(self):
        """
        Check if solution/explanation is shown.
        """
        solution_selector = '.solution-span div.detailed-solution'
        return self.q(css=solution_selector).is_present()

    def is_correct_choice_highlighted(self, correct_choices):
        """
        Check if correct answer/choice highlighted for choice group.
        """
        xpath = '//fieldset/div[contains(@class, "field")][{0}]/label[contains(@class, "choicegroup_correct")]'
        for choice in correct_choices:
            if not self.q(xpath=xpath.format(choice)).is_present():
                return False
        return True

    @property
    def problem_question(self):
        """
        Return the question text of the problem.
        """
        return self.q(css="div.problem .wrapper-problem-response legend").text[0]

    @property
    def problem_question_descriptions(self):
        """
        Return a list of question descriptions of the problem.
        """
        return self.q(css="div.problem .wrapper-problem-response .question-description").text

    @property
    def problem_progress_graded_value(self):
        """
        Return problem progress text which contains weight of problem, if it is graded, and the student's current score.
        """
        self.wait_for_element_visibility('.problem-progress', "Problem progress is visible")
        return self.q(css='.problem-progress').text[0]

    @property
    def status_sr_text(self):
        """
        Returns the text in the special "sr" region used for display status.
        """
        return self.q(css='#reader-feedback').text[0]

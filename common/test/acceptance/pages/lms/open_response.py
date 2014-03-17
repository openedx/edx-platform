"""
Open-ended response in the courseware.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise
from .rubric import RubricPage


class OpenResponsePage(PageObject):
    """
    Open-ended response in the courseware.
    """

    url = None

    def is_browser_on_page(self):
        return self.q(css='div.xmodule_CombinedOpenEndedModule').present

    @property
    def assessment_type(self):
        """
        Return the type of assessment currently active.
        Options are "self", "ai", or "peer"
        """
        labels = self.q(css='section#combined-open-ended-status>div.statusitem-current').text

        if len(labels) < 1:
            self.warning("Could not find assessment type label")

        # Provide some tolerance to UI changes
        label_compare = labels[0].lower().strip()

        if 'self' in label_compare:
            return 'self'
        elif 'ai' in label_compare:
            return 'ai'
        elif 'peer' in label_compare:
            return 'peer'
        else:
            raise ValueError("Unexpected assessment type: '{0}'".format(label_compare))

    @property
    def prompt(self):
        """
        Return an HTML string representing the essay prompt.
        """
        prompt_css = "section.open-ended-child>div.prompt"
        prompts = self.q(css=prompt_css).map(lambda el: el.get_attribute('innerHTML').strip()).results

        if len(prompts) == 0:
            self.warning("Could not find essay prompt on page.")
            return ""

        elif len(prompts) > 1:
            self.warning("Multiple essay prompts found on page; using the first one.")

        return prompts[0]

    @property
    def rubric(self):
        """
        Return a `RubricPage` for a self-assessment problem.
        If no rubric is available, raises a `BrokenPromise` exception.
        """
        rubric = RubricPage(self.browser)
        rubric.wait_for_page()
        return rubric

    @property
    def written_feedback(self):
        """
        Return the written feedback from the grader (if any).
        If no feedback available, returns None.
        """
        feedback = self.q(css='div.written-feedback').text

        if len(feedback) > 0:
            return feedback[0]
        else:
            return None

    @property
    def alert_message(self):
        """
        Alert message displayed to the user.
        """
        alerts = self.q(css="div.open-ended-alert").text

        if len(alerts) < 1:
            return ""
        else:
            return alerts[0]

    @property
    def grader_status(self):
        """
        Status message from the grader.
        If not present, return an empty string.
        """
        status_list = self.q(css='div.grader-status').text

        if len(status_list) < 1:
            self.warning("No grader status found")
            return ""

        elif len(status_list) > 1:
            self.warning("Multiple grader statuses found; returning the first one")

        return status_list[0]

    def set_response(self, response_str):
        """
        Input a response to the prompt.
        """
        input_css = "textarea.short-form-response"
        self.q(css=input_css).fill(response_str)

    def save_response(self):
        """
        Save the response for later submission.
        """
        self.q(css='input.save-button').first.click()
        EmptyPromise(
            lambda: 'save' in self.alert_message.lower(),
            "Status message saved"
        ).fulfill()

    def submit_response(self):
        """
        Submit a response for grading.
        """
        self.q(css='input.submit-button').first.click()

        # modal dialog confirmation
        self.q(css='button.ok-button').first.click()

        # Ensure that the submission completes
        self._wait_for_submitted(self.assessment_type)

    def _wait_for_submitted(self, assessment_type):
        """
        Wait for the submission to complete.
        `assessment_type` is either 'self', 'ai', or 'peer'
        """
        if assessment_type == 'self':
            RubricPage(self.browser).wait_for_page()

        elif assessment_type == 'ai' or assessment_type == "peer":
            EmptyPromise(
                lambda: self.grader_status != 'Unanswered',
                "Problem status is no longer 'unanswered'"
            ).fulfill()

        else:
            self.warning("Unrecognized assessment type '{0}'".format(assessment_type))
            EmptyPromise(lambda: True, "Unrecognized assessment type").fulfill()

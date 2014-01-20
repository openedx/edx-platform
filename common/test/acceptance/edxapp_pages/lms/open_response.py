"""
Open-ended response in the courseware.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, fulfill_after, fulfill_before


class OpenResponsePage(PageObject):
    """
    Open-ended response in the courseware.
    """

    name = "lms.open_response"

    def url(self):
        """
        Open-response isn't associated with a particular URL.
        """
        raise NotImplementedError

    def is_browser_on_page(self):
        return self.is_css_present('section.xmodule_CombinedOpenEndedModule')

    @property
    def assessment_type(self):
        """
        Return the type of assessment currently active.
        Options are "self", "ai", or "peer"
        """
        labels = self.css_text('section#combined-open-ended-status>div.statusitem-current')

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
        prompts = self.css_map(prompt_css, lambda el: el.html.strip())

        if len(prompts) == 0:
            self.warning("Could not find essay prompt on page.")
            return ""

        elif len(prompts) > 1:
            self.warning("Multiple essay prompts found on page; using the first one.")

        return prompts[0]

    @property
    def has_rubric(self):
        """
        Return a boolean indicating whether the rubric is available.
        """
        return self.is_css_present('div.rubric')

    @property
    def rubric_categories(self):
        """
        Return a list of categories available in the essay rubric.

        Example:
            ["Writing Applications", "Language Conventions"]

        The rubric is not always visible; if it's not available,
        this will return an empty list.
        """
        return self.css_text('span.rubric-category')

    @property
    def rubric_feedback(self):
        """
        Return a list of correct/incorrect feedback for each rubric category (e.g. from self-assessment).
        Example: ['correct', 'incorrect']

        If no feedback is available, returns an empty list.
        If feedback could not be interpreted (unexpected CSS class),
            the list will contain a `None` item.
        """

        # Get the green checkmark / red x labels
        # We need to filter out the similar-looking CSS classes
        # for the rubric items that are NOT marked correct/incorrect
        feedback_css = 'div.rubric-label>label'
        labels = [
            el_class for el_class in
            self.css_map(feedback_css, lambda el: el['class'])
            if el_class != 'rubric-elements-info'
        ]

        def map_feedback(css_class):
            """
            Map CSS classes on the labels to correct/incorrect
            """
            if 'choicegroup_incorrect' in css_class:
                return 'incorrect'
            elif 'choicegroup_correct' in css_class:
                return 'correct'
            else:
                return None

        return map(map_feedback, labels)

    @property
    def alert_message(self):
        """
        Alert message displayed to the user.
        """
        alerts = self.css_text("div.open-ended-alert")

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
        status_list = self.css_text('div.grader-status')

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
        self.css_fill(input_css, response_str)

    def save_response(self):
        """
        Save the response for later submission.
        """
        status_msg_shown = EmptyPromise(
            lambda: 'save' in self.alert_message.lower(),
            "Status message saved"
        )

        with fulfill_after(status_msg_shown):
            self.css_click('input.save-button')

    def submit_response(self):
        """
        Submit a response for grading.
        """
        with fulfill_after(self._submitted_promise(self.assessment_type)):
            with self.handle_alert():
                self.css_click('input.submit-button')

    def submit_self_assessment(self, scores):
        """
        Submit a self-assessment rubric.
        `scores` is a list of scores (0 to max score) for each category in the rubric.
        """

        # Warn if we have the wrong number of scores
        num_categories = len(self.rubric_categories)
        if len(scores) != num_categories:
            msg = "Recieved {0} scores but there are {1} rubric categories".format(
                len(scores), num_categories
            )
            self.warning(msg)

        # Set the score for each category
        for score_index in range(len(scores)):

            # Check that we have the enough radio buttons
            category_css = "div.rubric>ul.rubric-list:nth-of-type({0})".format(score_index + 1)
            if scores[score_index] > self.css_count(category_css + ' input.score-selection'):
                msg = "Tried to select score {0} but there are only {1} options".format(score_index, len(scores))
                self.warning(msg)

            # Check the radio button at the correct index
            else:
                input_css = (
                    category_css +
                    ">li.rubric-list-item:nth-of-type({0}) input.score-selection".format(scores[score_index] + 1)
                )
                self.css_check(input_css)

        # Wait for the button to become enabled
        button_css = 'input.submit-button'
        button_enabled = EmptyPromise(
            lambda: all(self.css_map(button_css, lambda el: not el['disabled'])),
            "Submit button enabled"
        )

        # Submit the assessment
        with fulfill_before(button_enabled):
            self.css_click(button_css)

    def _submitted_promise(self, assessment_type):
        """
        Return a `Promise` that the next step is visible after submitting.
        This will vary based on the type of assessment.

        `assessment_type` is either 'self', 'ai', or 'peer'
        """
        if assessment_type == 'self':
            return EmptyPromise(lambda: self.has_rubric, "Rubric has appeared")

        elif assessment_type == 'ai':
            return EmptyPromise(
                lambda: self.grader_status != 'Unanswered',
                "Problem status is no longer 'unanswered'"
            )

        elif assessment_type == 'peer':
            return EmptyPromise(lambda: False, "Peer assessment not yet implemented")

        else:
            self.warning("Unrecognized assessment type '{0}'".format(assessment_type))
            return EmptyPromise(lambda: True, "Unrecognized assessment type")

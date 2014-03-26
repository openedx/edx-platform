"""
Rubric for open-ended response problems, including calibration and peer-grading.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise


class ScoreMismatchError(Exception):
    """
    The provided scores do not match the rubric on the page.
    """
    pass


class RubricPage(PageObject):
    """
    Rubric for open-ended response problems, including calibration and peer-grading.
    """

    url = None

    def is_browser_on_page(self):
        """
        Return a boolean indicating whether the rubric is available.
        """
        return self.q(css='div.rubric').present

    @property
    def categories(self):
        """
        Return a list of categories available in the essay rubric.

        Example:
            ["Writing Applications", "Language Conventions"]

        The rubric is not always visible; if it's not available,
        this will return an empty list.
        """
        return self.q(css='span.rubric-category').text

    def set_scores(self, scores):
        """
        Set the rubric scores.  `scores` is a list of integers
        indicating the number of points in each category.

        For example, `scores` might be [0, 2, 1] if the student scored
        0 points in the first category, 2 points in the second category,
        and 1 point in the third category.

        If the number of scores does not match the number of categories,
        a `ScoreMismatchError` is raised.
        """
        # Warn if we have the wrong number of scores
        num_categories = self.categories
        if len(scores) != len(num_categories):
            raise ScoreMismatchError(
                "Received {0} scores but there are {1} rubric categories".format(
                    len(scores), num_categories))

        # Set the score for each category
        for score_index in range(len(scores)):
            # Check that we have the enough radio buttons
            category_css = "div.rubric>ul.rubric-list:nth-of-type({0})".format(score_index + 1)
            if scores[score_index] > len(self.q(css=category_css + ' input.score-selection').results):
                raise ScoreMismatchError(
                    "Tried to select score {0} but there are only {1} options".format(
                        score_index, len(scores)))

            # Check the radio button at the correct index
            else:
                input_css = (
                    category_css +
                    ">li.rubric-list-item:nth-of-type({0}) input.score-selection".format(scores[score_index] + 1)
                )

                EmptyPromise(lambda: self._select_score_radio_button(input_css), "Score selection failed.").fulfill()

    def _select_score_radio_button(self, radio_button_css):
        self.q(css=radio_button_css).first.click()
        return self.q(css=radio_button_css).selected

    @property
    def feedback(self):
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
            self.q(css=feedback_css).attrs('class')
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

    def submit(self, promise_check_type=None):
        """
        Submit the rubric.
        `promise_check_type` is either 'self', or 'peer'. If promise check is not required then don't pass any value.
        """
        # Wait for the button to become enabled
        button_css = 'input.submit-button'

        EmptyPromise(
            lambda: all(self.q(css=button_css).map(lambda el: not el.get_attribute('disabled')).results),
            "Submit button not enabled"
        ).fulfill()

        # Submit the assessment
        self.q(css=button_css).first.click()

        if promise_check_type == 'self':
            # Check if submitted rubric is available
            EmptyPromise(
                lambda: self.q(css='div.rubric-label>label').present, 'Submitted Rubric not available!'
            ).fulfill()
        elif promise_check_type == 'peer':
            # Check if we are ready for peer grading
            EmptyPromise(
                lambda: self.q(css='input.calibration-feedback-button').present, 'Not ready for peer grading!'
            ).fulfill()

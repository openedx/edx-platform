"""
Page that allows the student to grade calibration essays
(requirement for being allowed to grade peers).
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import Promise
from .rubric import RubricPage


class PeerCalibratePage(PageObject):
    """
    Grade calibration essays.
    """

    url = None

    def is_browser_on_page(self):

        def _is_correct_page():
            is_present = (
                self.q(css='div.peer-grading-tools').present or
                self.q(css='div.calibration-panel.current-state').present
            )
            return is_present, is_present

        return Promise(_is_correct_page, 'On the peer grading calibration page.').fulfill()

    def continue_to_grading(self):
        """
        Continue to peer grading after completing calibration.
        """
        self.q(css='input.calibration-feedback-button').first.click()

    @property
    def rubric(self):
        """
        Return a `RubricPage` for the calibration essay.
        If no rubric is available, raises a `BrokenPromise` exception.
        """
        rubric = RubricPage(self.browser)
        rubric.wait_for_page(timeout=60)
        return rubric

    @property
    def message(self):
        """
        Return a message shown to the user, or None if no message is available.
        """
        messages = self.q(css='div.peer-grading-tools > div.message-container > p').text
        if len(messages) < 1:
            return None
        else:
            return messages[0]

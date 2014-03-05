"""
Page that allows the student to grade calibration essays
(requirement for being allowed to grade peers).
"""

from bok_choy.page_object import PageObject
from .rubric import RubricPage


class PeerCalibratePage(PageObject):
    """
    Grade calibration essays.
    """

    url = None

    def is_browser_on_page(self):
        return (
            self.is_css_present('div.peer-grading-tools') or
            self.is_css_present('div.calibration-panel.current-state')
        )

    def continue_to_grading(self):
        """
        Continue to peer grading after completing calibration.
        """
        self.css_click('input.calibration-feedback-button')

    @property
    def rubric(self):
        """
        Return a `RubricPage` for the calibration essay.
        If no rubric is available, raises a `BrokenPromise` exception.
        """
        rubric = RubricPage(self.browser)
        rubric.wait_for_page()
        return rubric

    @property
    def message(self):
        """
        Return a message shown to the user, or None if no message is available.
        """
        messages = self.css_text('div.peer-grading-tools > div.message-container > p')
        if len(messages) < 1:
            return None
        else:
            return messages[0]

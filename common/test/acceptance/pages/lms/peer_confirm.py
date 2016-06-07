"""
Confirmation screen for peer calibration and grading.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import Promise


class PeerConfirmPage(PageObject):
    """
    Confirmation for peer calibration and grading.
    """

    url = None

    def is_browser_on_page(self):

        def _is_correct_page():
            is_present = self.q(css='section.calibration-interstitial-page').present
            return is_present, is_present

        return Promise(_is_correct_page, 'On the confirmation page for peer calibration and grading.').fulfill()

    def start(self, is_calibrating=False):
        """
        Continue to the next section after the confirmation page.
        If `is_calibrating` is false, try to continue to peer grading.
        Otherwise, try to continue to calibration grading.
        """
        if is_calibrating:
            css_selector = 'input.calibration-interstitial-page-button'
        else:
            css_selector = 'input.interstitial-page-button'
        self.q(css=css_selector).first.click()

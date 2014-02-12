"""
Confirmation screen for peer calibration and grading.
"""

from bok_choy.page_object import PageObject


class PeerConfirmPage(PageObject):
    """
    Confirmation for peer calibration and grading.
    """

    url = None

    def is_browser_on_page(self):
        return self.is_css_present('section.calibration-interstitial-page')

    def start(self, is_calibrating=False):
        """
        Continue to the next section after the confirmation page.
        If `is_calibrating` is false, try to continue to peer grading.
        Otherwise, try to continue to calibration grading.
        """
        self.css_click(
            'input.calibration-interstitial-page-button'
            if is_calibrating else 'input.interstitial-page-button'
        )

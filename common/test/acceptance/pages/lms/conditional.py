"""
Conditional Pages
"""
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, BrokenPromise

POLL_ANSWER = 'Yes, of course'


class ConditionalPage(PageObject):
    """
    View of conditional page.
    """

    url = None

    def is_browser_on_page(self):
        """
        Returns True if the browser is currently on the right page.
        """
        # This is all a hack to work around the fact that there's no way to adjust the
        # timeout parameters for self.q
        def check_fn():
            return self.q(css='.conditional-wrapper').visible
        try:
            EmptyPromise(
                check_fn,
                "On conditional page",
            ).fulfill()
            return True
        except BrokenPromise:
            return False

    def is_content_visible(self):
        """
        Returns True if the conditional's content has been revealed,
        False otherwise
        """
        def check_fn():
            return self.q(css='.hidden-contents').visible
        try:
            EmptyPromise(
                check_fn,
                "Conditional is visible",
            ).fulfill()
            return True
        except BrokenPromise:
            return False

    def fill_in_poll(self):
        """
        Fills in a poll on the same page as the conditional
        with the answer that matches POLL_ANSWER
        """
        text_selector = '.poll_answer .text'

        text_options = self.q(css=text_selector).text

        # Out of the possible poll answers, we want
        # to select the one that matches POLL_ANSWER and click it.
        for idx, text in enumerate(text_options):
            if text == POLL_ANSWER:
                self.q(css=text_selector).nth(idx).click()

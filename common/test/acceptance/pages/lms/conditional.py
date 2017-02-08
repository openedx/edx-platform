"""
Conditional Pages
"""
from bok_choy.page_object import PageObject

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
        return self.q(css='.conditional-wrapper').visible

    def is_content_visible(self):
        """
        Returns True if the conditional's content has been revealed,
        False otherwise
        """
        return self.q(css='.hidden-contents').visible

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

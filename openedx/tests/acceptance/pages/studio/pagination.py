"""
Mixin to include for Paginated container pages
"""
from selenium.webdriver.common.keys import Keys


class PaginatedMixin(object):
    """
    Mixin class used for paginated page tests.
    """
    def nav_disabled(self, position, arrows=('next', 'previous')):
        """
        Verifies that pagination nav is disabled. Position can be 'top' or 'bottom'.

        `top` is the header, `bottom` is the footer.

        To specify a specific arrow, pass an iterable with a single element, 'next' or 'previous'.
        """
        return all([
            self.q(css='nav.%s * .%s-page-link.is-disabled' % (position, arrow))
            for arrow in arrows
        ])

    def move_back(self, position):
        """
        Clicks one of the forward nav buttons. Position can be 'top' or 'bottom'.
        """
        self.q(css='nav.%s * .previous-page-link' % position)[0].click()
        self.wait_until_ready()

    def move_forward(self, position):
        """
        Clicks one of the forward nav buttons. Position can be 'top' or 'bottom'.
        """
        self.q(css='nav.%s * .next-page-link' % position)[0].click()
        self.wait_until_ready()

    def go_to_page(self, number):
        """
        Enter a number into the page number input field, and then try to navigate to it.
        """
        page_input = self.q(css="#page-number-input")[0]
        page_input.click()
        page_input.send_keys(str(number))
        page_input.send_keys(Keys.RETURN)
        self.wait_until_ready()

    def get_page_number(self):
        """
        Returns the page number as the page represents it, in string form.
        """
        return self.q(css="span.current-page")[0].get_attribute('innerHTML')

    def check_page_unchanged(self, first_block_name):
        """
        Used to make sure that a page has not transitioned after a bogus number is given.
        """
        if not self.xblocks[0].name == first_block_name:
            return False
        if not self.q(css='#page-number-input')[0].get_attribute('value') == '':
            return False
        return True

"""Mode creation page (used to add modes to courses during testing)."""

import re
import urllib

from bok_choy.page_object import PageObject
from . import BASE_URL


class ModeCreationPage(PageObject):
    """The mode creation page.

    When allowed by the Django settings file, visiting this page allows modes to be
    created for an existing course.
    """

    def __init__(self, browser, course_id, mode_slug=None, mode_display_name=None, min_price=None, suggested_prices=None, currency=None):
        """The mode creation page is an endpoint for HTTP GET requests.

        By default, it will create an 'honor' mode for the given course with display name
        'Honor Code', a minimum price of 0, no suggested prices, and using USD as the currency.

        Arguments:
            browser (Browser): The browser instance.
            course_id (unicode): The ID of the course for which modes are to be created.

        Keyword Arguments:
            mode_slug (str): The mode to add, either 'honor', 'verified', or 'professional'
            mode_display_name (str): Describes the new course mode
            min_price (int): The minimum price a user must pay to enroll in the new course mode
            suggested_prices (str): Comma-separated prices to suggest to the user.
            currency (str): The currency in which to list prices.
        """
        super(ModeCreationPage, self).__init__(browser)

        self._course_id = course_id
        self._parameters = {}

        if mode_slug is not None:
            self._parameters['mode_slug'] = mode_slug

        if mode_display_name is not None:
            self._parameters['mode_display_name'] = mode_display_name

        if min_price is not None:
            self._parameters['min_price'] = min_price

        if suggested_prices is not None:
            self._parameters['suggested_prices'] = suggested_prices

        if currency is not None:
            self._parameters['currency'] = currency

    @property
    def url(self):
        """Construct the mode creation URL."""
        url = '{base}/course_modes/create_mode/{course_id}/'.format(
            base=BASE_URL,
            course_id=self._course_id
        )

        query_string = urllib.urlencode(self._parameters)
        if query_string:
            url += '?' + query_string

        return url

    def is_browser_on_page(self):
        message = self.q(css='BODY').text[0]
        match = re.search(r'Mode ([^$]+) created for ([^$]+).$', message)
        return True if match else False

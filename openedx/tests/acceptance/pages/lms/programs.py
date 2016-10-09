"""LMS-hosted Programs pages"""
from bok_choy.page_object import PageObject

from openedx.tests.acceptance.pages.lms import BASE_URL


class ProgramListingPage(PageObject):
    """Program listing page."""
    url = BASE_URL + '/dashboard/programs/'

    def is_browser_on_page(self):
        return self.q(css='.program-list-wrapper').present

    @property
    def are_cards_present(self):
        """Check whether program cards are present."""
        return self.q(css='.program-card').present

    @property
    def is_sidebar_present(self):
        """Check whether sidebar is present."""
        return self.q(css='.sidebar').present


class ProgramDetailsPage(PageObject):
    """Program details page."""
    program_id = 123
    url = BASE_URL + '/dashboard/programs/{}/program-name/'.format(program_id)

    def is_browser_on_page(self):
        return self.q(css='.js-program-details-wrapper').present

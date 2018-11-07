# -*- coding: utf-8 -*-
"""
End-to-end tests for admin change view.
"""

from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.admin import ChangeUserAdminPage
from common.test.acceptance.tests.helpers import AcceptanceTest


class UnicodeUsernameAdminTest(AcceptanceTest):
    """
    Tests if it is possible to update users with unicode usernames in the admin.
    """
    shard = 21

    # The word below reads "Omar II", in Arabic. It also contains a space and
    # an Eastern Arabic Number another option is to use the Esperanto fake
    # language but this was used instead to test non-western letters.
    FIXTURE_USERNAME = u'عمر ٢'

    # From the db fixture `unicode_user.json`
    FIXTURE_USER_ID = 1000

    def setUp(self):
        """
        Initializes and visits the change user admin page as a superuser.
        """
        # Some state is constructed by the parent setUp() routine
        super(UnicodeUsernameAdminTest, self).setUp()

        AutoAuthPage(self.browser, staff=True, superuser=True).visit()

        # Load page objects for use by the tests
        self.page = ChangeUserAdminPage(self.browser, self.FIXTURE_USER_ID)

        # Navigate to the index page and get testing!
        self.page.visit()

    def test_update_first_name(self):
        """
        As a superuser I should be able to update the first name of a user with unicode username.
        """
        self.assertNotEqual(self.page.first_name, 'John')
        self.assertEquals(self.page.username, self.FIXTURE_USERNAME)

        self.page.change_first_name('John')

        self.assertFalse(self.page.is_browser_on_page(), 'Should redirect to the admin user list view on success')

        # Visit the page again to verify changes
        self.page.visit()

        self.assertEquals(self.page.first_name, 'John', 'The first name should be updated')

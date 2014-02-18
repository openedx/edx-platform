from bok_choy.web_app_test import WebAppTest
from bok_choy.promise import fulfill, Promise

from .helpers import UniqueCourseTest
from ..pages.lms.dashboard import DashboardPage
from ..pages.lms.logout import LogoutPage
from ..pages.studio.auto_auth import AutoAuthPage


class LanguageTest(UniqueCourseTest):
    """
    Tests that the change language functionality on the dashboard works.
    """

    def setUp(self):
        """
        Visit the dashboard page.
        """
        super(LanguageTest, self).setUp()

        # Log in and visit the dashboard page
        self.auto_auth = AutoAuthPage(
            self.browser, course_id=self.course_id, username=self.unique_id[0:10]
        ).visit()
        self.dashboard_page = DashboardPage(self.browser).visit()

    def test_change_lang(self):
        # By default, should not be using the dummy language
        self.assertFalse(self.dashboard_page.is_dummy_lang)

        # Change language to Dummy Esperanto
        self.dashboard_page.change_language('eo')
        self.assertTrue(self.dashboard_page.is_dummy_lang)

    def test_language_persists(self):

        # Change language to Dummy Esperanto
        self.dashboard_page.change_language('eo')

        # Log out and log back in
        LogoutPage(self.browser).visit()
        self.auto_auth.visit()

        # Return to the dashboard and verify that we still see the dummy language
        self.dashboard_page.visit()
        self.assertTrue(self.dashboard_page.is_dummy_lang)

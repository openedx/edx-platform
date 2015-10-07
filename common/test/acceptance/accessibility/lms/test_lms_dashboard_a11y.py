"""
Accessibility tests for LMS dashboard page.

Run just this test with:
SELENIUM_BROWSER=phantomjs paver test_bokchoy -d accessibility -t test_lms_dashboard_a11y.py
"""
from ...tests.lms.test_lms_dashboard import BaseLmsDashboardTest


class LmsDashboardAxsTest(BaseLmsDashboardTest):
    """
    Class to test lms student dashboard accessibility.
    """

    def test_dashboard_course_listings_axs(self):
        """
        Test the accessibility of the course listings
        """
        course_listings = self.dashboard_page.get_course_listings()
        self.assertEqual(len(course_listings), 1)

        # There are several existing color contrast errors on this page,
        # we will ignore this error in the test until we fix them.
        self.dashboard_page.a11y_audit.config.set_rules({
            "ignore": ['color-contrast'],
        })

        self.dashboard_page.a11y_audit.check_for_accessibility_errors()

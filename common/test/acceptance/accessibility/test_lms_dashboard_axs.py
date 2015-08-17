"""
Accessibility tests for LMS dashboard page.

Run just this test with:
SELENIUM_BROWSER=phantomjs paver test_bokchoy -d accessibility -t test_lms_dashboard_axs.py
"""
from ..tests.lms.test_lms_dashboard import BaseLmsDashboardTest


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

        report = self.dashboard_page.do_axs_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))

        result = report[0]
        # Verify that this page has no accessibility errors.
        self.assertEqual(0, len(result.errors))
        # Verify that this page currently has 2 accessibility warnings.
        self.assertEqual(2, len(result.warnings))
        # And that these are the warnings that the page currently gives.
        for warning in result.warnings:
            self.assertTrue(
                warning.startswith(('Warning: AX_FOCUS_01', 'Warning: AX_COLOR_01',)),
                msg="Unexpected warning: {}".format(warning))

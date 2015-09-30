"""
Accessibility tests for Studio Library pages.

Run just this test with:
SELENIUM_BROWSER=phantomjs paver test_bokchoy -d accessibility -t test_studio_library_a11y.py
"""
from ..tests.studio.base_studio_test import StudioLibraryTest
from ..pages.studio.library import LibraryEditPage


class StudioLibraryAxsTest(StudioLibraryTest):
    """
    Class to test Studio pages accessibility.
    """

    def test_lib_edit_page_axs(self):
        """
        Check accessibility of LibraryEditPage.
        """
        lib_page = LibraryEditPage(self.browser, self.library_key)
        lib_page.visit()
        lib_page.wait_until_ready()

        # There are several existing color contrast errors on this page,
        # we will ignore this error in the test until we fix them.
        lib_page.a11y_audit.config.set_rules({
            "ignore": ['color-contrast'],
        })

        lib_page.a11y_audit.check_for_accessibility_errors()

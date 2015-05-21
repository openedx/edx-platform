"""
Accessibility tests for Studio Library pages.

Run just this test with:
SELENIUM_BROWSER=phantomjs paver test_bokchoy -d accessibility -t test_studio_library_axs.py
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
        report = lib_page.do_axs_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))

        result = report[0]
        # Verify that this page has no accessibility errors.
        self.assertEqual(0, len(result.errors))
        # Verify that this page currently has 3 accessibility warnings.
        self.assertEqual(3, len(result.warnings))
        # And that these are the warnings that the page currently gives.
        for warning in result.warnings:
            self.assertTrue(
                warning.startswith(('Warning: AX_FOCUS_01', 'Warning: AX_COLOR_01', 'Warning: AX_IMAGE_01',)),
                msg="Unexpected warning: {}".format(warning))

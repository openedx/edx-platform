"""
Acceptance tests for Content Libraries in Studio
"""


from common.test.acceptance.pages.studio.library import LibraryEditPage
from common.test.acceptance.tests.studio.base_studio_test import StudioLibraryTest
from openedx.core.lib.tests import attr


@attr('a11y')
class StudioLibraryA11yTest(StudioLibraryTest):
    """
    Class to test Studio pages accessibility.
    """

    def test_lib_edit_page_a11y(self):
        """
        Check accessibility of LibraryEditPage.
        """
        lib_page = LibraryEditPage(self.browser, self.library_key)
        lib_page.visit()
        lib_page.wait_until_ready()

        lib_page.a11y_audit.config.set_rules({
            "ignore": [
                'link-href',  # TODO: AC-590
                'duplicate-id-aria',  # TODO: AC-940
                'heading-order',  # TODO: AC-933
                'landmark-complementary-is-top-level',  # TODO: AC-939
                'region'  # TODO: AC-932
            ],
        })

        lib_page.a11y_audit.check_for_accessibility_errors()

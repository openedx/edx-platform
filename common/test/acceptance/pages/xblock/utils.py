"""
Utility methods useful for XBlock page tests.
"""
from bok_choy.promise import Promise


def wait_for_xblock_initialization(page, xblock_css):
    """
    Wait for the xblock with the given CSS to finish initializing.
    """
    def _is_finished_loading():
        # Wait for the xblock javascript to finish initializing
        is_done = page.browser.execute_script("return $({!r}).data('initialized')".format(xblock_css))
        return (is_done, is_done)

    return Promise(_is_finished_loading, 'Finished initializing the xblock.').fulfill()

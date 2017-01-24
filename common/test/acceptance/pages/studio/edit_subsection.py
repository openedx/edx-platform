"""
Edit Subsection page in Studio
"""

from bok_choy.page_object import PageObject


class SubsectionPage(PageObject):
    """
    Edit Subsection page in Studio
    """

    def is_browser_on_page(self):
        return self.q(css='body.view-subsection').present

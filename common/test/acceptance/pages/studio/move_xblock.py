"""
Move XBlock Modal Page Object
"""


from bok_choy.page_object import PageObject

from common.test.acceptance.pages.common.utils import click_css


class MoveModalView(PageObject):
    """
    A base class for move xblock
    """

    def is_browser_on_page(self):
        return self.q(css='.modal-window.move-modal').present

    def url(self):
        """
        Returns None because this is not directly accessible via URL.
        """
        return None

    def save(self):
        """
        Clicks save button.
        """
        click_css(self, 'a.action-save')

    def cancel(self):
        """
        Clicks cancel button.
        """
        click_css(self, 'a.action-cancel', require_notification=False)

    def click_forward_button(self, source_index):
        """
        Click forward button at specified `source_index`.
        """
        css = '.move-modal .xblock-items-container .xblock-item'
        self.q(css='.button-forward').nth(source_index).click()
        self.wait_for(
            lambda: len(self.q(css=css).results) > 0, description='children are visible'
        )

    def click_move_button(self):
        """
        Click move button.
        """
        self.q(css='.modal-actions .action-move').first.click()

    @property
    def is_move_button_enabled(self):
        """
        Returns True if move button on modal is enabled else False.
        """
        return not self.q(css='.modal-actions .action-move.is-disabled').present

    @property
    def children_category(self):
        """
        Get displayed children category.
        """
        return self.q(css='.xblock-items-container').attrs('data-items-category')[0]

    def navigate_to_category(self, category, navigation_options):
        """
        Navigates to specifec `category` for a specified `source_index`.
        """
        child_category = self.children_category
        while child_category != category:
            self.click_forward_button(navigation_options[child_category])
            child_category = self.children_category

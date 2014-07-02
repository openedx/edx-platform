"""
Unit page in Studio
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, Promise

from . import BASE_URL
from .container import ContainerPage


class UnitPage(PageObject):
    """
    Unit page in Studio
    """

    def __init__(self, browser, unit_locator):
        super(UnitPage, self).__init__(browser)
        self.unit_locator = unit_locator

    @property
    def url(self):
        """URL to the pages UI in a course."""
        return "{}/unit/{}".format(BASE_URL, self.unit_locator)

    def is_browser_on_page(self):

        def _is_finished_loading():
            # Wait until all components have been loaded
            number_of_leaf_xblocks = len(self.q(css='{} .xblock-author_view,.xblock-student_view'.format(Component.BODY_SELECTOR)).results)
            is_done = len(self.q(css=Component.BODY_SELECTOR).results) == number_of_leaf_xblocks
            return (is_done, is_done)

        # First make sure that an element with the view-unit class is present on the page,
        # and then wait to make sure that the xblocks are all there
        return (
            self.q(css='body.view-unit').present and
            Promise(_is_finished_loading, 'Finished rendering the xblocks in the unit.').fulfill()
        )

    @property
    def components(self):
        """
        Return a list of components loaded on the unit page.
        """
        return self.q(css=Component.BODY_SELECTOR).map(
            lambda el: Component(self.browser, el.get_attribute('data-locator'))).results

    def edit_draft(self):
        """
        Started editing a draft of this unit.
        """
        EmptyPromise(
            lambda: self.q(css='.create-draft').present,
            'Wait for edit draft link to be present'
        ).fulfill()

        self.q(css='.create-draft').first.click()

        EmptyPromise(
            lambda: self.q(css='.editing-draft-alert').present,
            'Wait for draft mode to be activated'
        ).fulfill()


class Component(PageObject):
    """
    A PageObject representing an XBlock child on the Studio UnitPage (including
    the editing controls).
    """
    url = None
    BODY_SELECTOR = '.component'
    NAME_SELECTOR = '.component-header'

    def __init__(self, browser, locator):
        super(Component, self).__init__(browser)
        self.locator = locator

    def is_browser_on_page(self):
        return self.q(css='{}[data-locator="{}"]'.format(self.BODY_SELECTOR, self.locator)).present

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to this particular `CourseOutlineChild` context
        """
        return '{}[data-locator="{}"] {}'.format(
            self.BODY_SELECTOR,
            self.locator,
            selector
        )

    @property
    def name(self):
        titles = self.q(css=self._bounded_selector(self.NAME_SELECTOR)).text
        if titles:
            return titles[0]
        else:
            return None

    @property
    def preview_selector(self):
        return self._bounded_selector('.xblock-author_view,.xblock-student_view')

    def edit(self):
        """
        Clicks the "edit" button for the first component on the page.

        Same as the implementation in unit.py, unit and component pages will be merging.
        """
        self.q(css=self._bounded_selector('.edit-button')).first.click()
        EmptyPromise(
            lambda: self.q(css='.xblock-studio_view').present,
            'Wait for the Studio editor to be present'
        ).fulfill()

        return self

    @property
    def editor_selector(self):
        return '.xblock-studio_view'

    def go_to_container(self):
        """
        Open the container page linked to by this component, and return
        an initialized :class:`.ContainerPage` for that xblock.
        """
        return ContainerPage(self.browser, self.locator).visit()

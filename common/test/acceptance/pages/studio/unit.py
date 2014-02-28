"""
Unit page in Studio
"""

from bok_choy.page_object import PageObject
from bok_choy.query import SubQuery
from bok_choy.promise import EmptyPromise, fulfill

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
        # Wait until all components have been loaded
        number_of_leaf_xblocks = len(self.q(css='{} .xblock-student_view'.format(Component.BODY_SELECTOR)))
        number_of_container_xblocks = len(self.q(css='{} .wrapper-xblock'.format(Component.BODY_SELECTOR)))
        return (
            self.is_css_present('body.view-unit') and
            len(self.q(css=Component.BODY_SELECTOR)) == number_of_leaf_xblocks + number_of_container_xblocks
        )

    @property
    def components(self):
        """
        Return a list of components loaded on the unit page.
        """
        return self.q(css=Component.BODY_SELECTOR).map(lambda el: Component(self.browser, el['data-locator'])).results

    def edit_draft(self):
        """
        Started editing a draft of this unit.
        """
        fulfill(EmptyPromise(
            lambda: self.q(css='.create-draft').present,
            'Wait for edit draft link to be present'
        ))
        self.q(css='.create-draft').click()
        fulfill(EmptyPromise(
            lambda: self.q(css='.editing-draft-alert').present,
            'Wait for draft mode to be activated'
        ))


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
        return self.is_css_present('{}[data-locator="{}"]'.format(self.BODY_SELECTOR, self.locator))

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
        titles = self.css_text(self._bounded_selector(self.NAME_SELECTOR))
        if titles:
            return titles[0]
        else:
            return None

    @property
    def preview_selector(self):
        return self._bounded_selector('.xblock-student_view')

    def edit(self):
        self.css_click(self._bounded_selector('.edit-button'))
        fulfill(EmptyPromise(
            lambda: all(
                self.q(css=self._bounded_selector('.component-editor'))
                    .map(lambda el: el.visible)
                    .results
                ),
            "Verify that the editor for component {} has been expanded".format(self.locator)
        ))
        return self

    @property
    def editor_selector(self):
        return self._bounded_selector('.xblock-studio_view')

    def go_to_container(self):
        """
        Open the container page linked to by this component, and return
        an initialized :class:`.ContainerPage` for that xblock.
        """
        return ContainerPage(self.browser, self.locator).visit()

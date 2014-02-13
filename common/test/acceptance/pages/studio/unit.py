"""
Unit page in Studio
"""

from bok_choy.page_object import PageObject
from bok_choy.query import SubQuery
from bok_choy.promise import EmptyPromise, fulfill

from . import BASE_URL


class UnitPage(PageObject):
    """
    Unit page in Studio
    """

    def __init__(self, browser, unit_locator):
        super(UnitPage, self).__init__(browser)
        self.unit_locator = unit_locator

    @property
    def url(self):
        """URL to the static pages UI in a course."""
        return "{}/unit/{}".format(BASE_URL, self.unit_locator)

    def is_browser_on_page(self):
        return self.is_css_present('body.view-unit')

    def component(self, title):
        return Component(
            self.browser,
            self.q(css=Component.BODY_SELECTOR).filter(
                SubQuery(css=Component.NAME_SELECTOR).filter(text=title)
            )[0]['data-locator']
        )


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

"""
Course Outline page in Studio.
"""
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from .course_page import CoursePage
from .unit import UnitPage

class CourseOutlineContainer(object):
    """
    A mixin to a CourseOutline page object that adds the ability to load
    a child page object by title.

    CHILD_CLASS must be a :class:`CourseOutlineChild` subclass.
    """
    CHILD_CLASS = None

    def child(self, title, child_class=None):
        if not child_class:
            child_class = self.CHILD_CLASS
        return child_class(
            self.browser,
            self.q(css=child_class.BODY_SELECTOR).filter()
        )


class CourseOutlineChild(PageObject):
    """
    A mixin to a CourseOutline page object that will be used as a child of
    :class:`CourseOutlineContainer`.
    """
    NAME_SELECTOR = None
    BODY_SELECTOR = None

    def __init__(self, browser, locator):
        super(CourseOutlineChild, self).__init__(browser)
        self.locator = locator

    def is_browser_on_page(self):
        return self.q(css='{}[data-locator="{}"]'.format(self.BODY_SELECTOR, self.locator)).present

    @property
    def name(self):
        """
        Return the display name of this object.
        """
        titles = self.q(css=self._bounded_selector(self.NAME_SELECTOR)).text
        if titles:
            return titles[0]
        else:
            return None

    def __repr__(self):
        return "{}(<browser>, {!r})".format(self.__class__.__name__, self.locator)

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to this particular `CourseOutlineChild` context
        """
        return '{}[data-locator="{}"] {}'.format(
            self.BODY_SELECTOR,
            self.locator,
            selector
        )


class CourseOutlineUnit(CourseOutlineChild):
    """
    PageObject that wraps a unit link on the Studio Course Overview page.
    """
    url = None
    BODY_SELECTOR = '.courseware-unit'
    NAME_SELECTOR = '.unit-name'

    def go_to(self):
        """
        Open the unit page linked to by this unit link, and return
        an initialized :class:`.UnitPage` for that unit.
        """
        return UnitPage(self.browser, self.locator).visit()


class CourseOutlineSubsection(CourseOutlineChild, CourseOutlineContainer):
    """
    :class`.PageObject` that wraps a subsection block on the Studio Course Overview page.
    """
    url = None

    BODY_SELECTOR = '.courseware-subsection'
    NAME_SELECTOR = '.subsection-name-value'
    CHILD_CLASS = CourseOutlineUnit

    def unit(self, title):
        """
        Return the :class:`.CourseOutlineUnit with the title `title`.
        """
        return self.child(title)

    def toggle_expand(self):
        """
        Toggle the expansion of this subsection.
        """
        self.disable_jquery_animations()

        def subsection_expanded():
            return all(
                self.q(css=self._bounded_selector('.new-unit-item'))
                    .map(lambda el: el.visible)
                    .results
            )

        currently_expanded = subsection_expanded()

        self.css_click(self._bounded_selector('.expand-collapse'))
        fulfill(EmptyPromise(
            lambda: subsection_expanded() != currently_expanded,
            "Check that the subsection {} has been toggled".format(self.locator),
        ))
        return self


class CourseOutlineSection(CourseOutlineChild, CourseOutlineContainer):
    """
    :class`.PageObject` that wraps a section block on the Studio Course Overview page.
    """
    url = None
    BODY_SELECTOR = '.courseware-section'
    NAME_SELECTOR = '.section-name-span'
    CHILD_CLASS = CourseOutlineSubsection

    def subsection(self, title):
        """
        Return the :class:`.CourseOutlineSubsection` with the title `title`.
        """
        return self.child(title)


class CourseOutlinePage(CoursePage, CourseOutlineContainer):
    """
    Course Outline page in Studio.
    """
    url_path = "course"
    CHILD_CLASS = CourseOutlineSection

    def is_browser_on_page(self):
        return self.q(css='body.view-outline').present

    def section(self, title):
        """
        Return the :class:`.CourseOutlineSection` with the title `title`.
        """
        return self.child(title)

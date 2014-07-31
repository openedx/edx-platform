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
        """

        :type self: object
        """
        if not child_class:
            child_class = self.CHILD_CLASS

        return child_class(
            self.browser,
            self.q(css=child_class.BODY_SELECTOR).filter(
                lambda el: title in [inner.text for inner in
                                     el.find_elements_by_css_selector(child_class.NAME_SELECTOR)]
            ).attrs('data-locator')[0]
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

    def is_browser_on_page(self):
        return self.q(css=self.BODY_SELECTOR).present


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
        self.browser.execute_script("jQuery.fx.off = true;")

        def subsection_expanded():
            return all(
                self.q(css=self._bounded_selector('.new-unit-item'))
                .map(lambda el: el.is_displayed())
                .results
            )

        currently_expanded = subsection_expanded()

        self.q(css=self._bounded_selector('.expand-collapse')).first.click()

        EmptyPromise(
            lambda: subsection_expanded() != currently_expanded,
            "Check that the subsection {} has been toggled".format(self.locator)
        ).fulfill()

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

    def click_section_name(self, parent_css=''):
        """
        Find and click on first section name in course outline
        """
        self.q(css='{} .section-name'.format(parent_css)).first.click()

    def get_section_name(self, parent_css='', page_refresh=False):
        """
        Get the list of names of all sections present
        """
        if page_refresh:
            self.browser.refresh()
        return self.q(css='{} .section-name'.format(parent_css)).text

    def section_name_edit_form_present(self, parent_css=''):
        """
        Check that section name edit form present
        """
        return self.q(css='{} .section-name input'.format(parent_css)).present

    def change_section_name(self, new_name, parent_css=''):
        """
        Change section name of first section present in course outline
        """
        self.click_section_name(parent_css)
        self.q(css='{} .section-name input'.format(parent_css)).first.fill(new_name)
        self.q(css='{} .section-name .save-button'.format(parent_css)).first.click()
        self.wait_for_ajax()

    def click_release_date(self):
        """
        Open release date edit modal of first section in course outline
        """
        self.q(css='div.section-published-date a.edit-release-date').first.click()

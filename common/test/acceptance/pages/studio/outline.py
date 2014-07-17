"""
Course Outline page in Studio.
"""
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from .course_page import CoursePage
from .container import ContainerPage
from .utils import set_input_value_and_save, click_css


class CourseOutlineItem(object):
    """
    A mixin class for any :class:`PageObject` shown in a course outline.
    """
    BODY_SELECTOR = None
    EDIT_BUTTON_SELECTOR = '.xblock-title .xblock-field-value-edit'
    NAME_SELECTOR = '.xblock-title .xblock-field-value'
    NAME_INPUT_SELECTOR = '.xblock-title .xblock-field-input'

    def __repr__(self):
        return "{}(<browser>, {!r})".format(self.__class__.__name__, self.locator)

    def _bounded_selector(self, selector):
        """
        Returns `selector`, but limited to this particular `CourseOutlineItem` context
        """
        return '{}[data-locator="{}"] {}'.format(
            self.BODY_SELECTOR,
            self.locator,
            selector
        )

    @property
    def name(self):
        """
        Returns the display name of this object.
        """
        name_element = self.q(css=self._bounded_selector(self.NAME_SELECTOR)).first
        if name_element:
            return name_element.text[0]
        else:
            return None

    def change_name(self, new_name):
        """
        Changes the container's name.
        """
        self.q(css=self._bounded_selector(self.EDIT_BUTTON_SELECTOR)).first.click()
        set_input_value_and_save(self, self._bounded_selector(self.NAME_INPUT_SELECTOR), new_name)
        self.wait_for_ajax()

    def in_editable_form(self):
        """
        Return whether this outline item's display name is in its editable form.
        """
        return "is-hidden" not in self.q(css=self._bounded_selector(self.NAME_INPUT_SELECTOR)).first.attrs("class")


class CourseOutlineContainer(CourseOutlineItem):
    """
    A mixin to a CourseOutline page object that adds the ability to load
    a child page object by title or by index.

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

    def children(self, child_class=None):
        """
        Returns all the children page objects of class child_class.
        """
        if not child_class:
            child_class = self.CHILD_CLASS

        children = []
        for child_element in self.q(css=child_class.BODY_SELECTOR):
            children.append(child_class(self.browser, child_element.get_attribute('data-locator')))
        return children

    def child_at(self, index, child_class=None):
        """
        Returns the child at the specified index.
        :type self: object
        """
        if not child_class:
            child_class = self.CHILD_CLASS

        return self.children(child_class)[index]

    def add_child(self, require_notification=True):
        """
        Adds a child to this xblock, waiting for notifications.
        """
        click_css(
            self,
            self._bounded_selector(".add-xblock-component a.add-button"),
            require_notification=require_notification,
        )


class CourseOutlineChild(PageObject, CourseOutlineItem):
    """
    A page object that will be used as a child of :class:`CourseOutlineContainer`.
    """
    def __init__(self, browser, locator):
        super(CourseOutlineChild, self).__init__(browser)
        self.locator = locator

    def is_browser_on_page(self):
        return self.q(css='{}[data-locator="{}"]'.format(self.BODY_SELECTOR, self.locator)).present


class CourseOutlineUnit(CourseOutlineChild):
    """
    PageObject that wraps a unit link on the Studio Course Outline page.
    """
    url = None
    BODY_SELECTOR = '.outline-item-unit'
    NAME_SELECTOR = '.xblock-title a'

    def go_to(self):
        """
        Open the container page linked to by this unit link, and return
        an initialized :class:`.ContainerPage` for that unit.
        """
        return ContainerPage(self.browser, self.locator).visit()


class CourseOutlineSubsection(CourseOutlineChild, CourseOutlineContainer):
    """
    :class`.PageObject` that wraps a subsection block on the Studio Course Outline page.
    """
    url = None

    BODY_SELECTOR = '.outline-item-subsection'
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
            add_button = self.q(css=self._bounded_selector('.add-button')).first.results
            return add_button and add_button[0].is_displayed()

        currently_expanded = subsection_expanded()

        self.q(css=self._bounded_selector('.ui-toggle-expansion')).first.click()

        EmptyPromise(
            lambda: subsection_expanded() != currently_expanded,
            "Check that the subsection {} has been toggled".format(self.locator)
        ).fulfill()

        return self

    def add_unit(self):
        self.add_child(require_notification=False)


class CourseOutlineSection(CourseOutlineChild, CourseOutlineContainer):
    """
    :class`.PageObject` that wraps a section block on the Studio Course Outline page.
    """
    url = None
    BODY_SELECTOR = '.outline-item-section'
    CHILD_CLASS = CourseOutlineSubsection

    def subsection(self, title):
        """
        Return the :class:`.CourseOutlineSubsection` with the title `title`.
        """
        return self.child(title)

    def subsections(self):
        return self.children()

    def subsection_at(self, index):
        """
        Returns the :class`.CourseOutlineSubsection` at the specified index.
        """
        return self.child_at(index)

    def add_subsection(self):
        self.add_child()


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

    def section_at(self, index):
        """
        Returns the :class:`.CourseOutlineSection` at the specified index.
        """
        return self.child_at(index)

    def sections(self):
        """
        Returns the sections of this course outline page.
        """
        return self.children()

    def add_section_from_top_button(self):
        """
        Clicks the button for adding a section which resides at the top of the screen, waiting for notifications.
        """
        click_css(self, '.wrapper-mast nav.nav-actions .add-button')

    def add_section_from_bottom_button(self):
        """
        Clicks the button for adding a section which resides at the bottom of the screen, waiting for notifications.
        """
        click_css(self, '.course-outline > .add-xblock-component .add-button')

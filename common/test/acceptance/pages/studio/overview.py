"""
Course Outline page in Studio.
"""
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from .course_page import CoursePage
from .container import ContainerPage
from .utils import set_input_value_and_save, click_css, confirm_prompt, set_input_value


class CourseOutlineItem(object):
    """
    A mixin class for any :class:`PageObject` shown in a course outline.
    """
    BODY_SELECTOR = None
    EDIT_BUTTON_SELECTOR = '.xblock-field-value-edit'
    NAME_SELECTOR = '.xblock-title .xblock-field-value'
    NAME_INPUT_SELECTOR = '.xblock-field-input'
    NAME_FIELD_WRAPPER_SELECTOR = '.xblock-title .wrapper-xblock-field'

    def __repr__(self):
        # CourseOutlineItem is also used as a mixin for CourseOutlinePage, which doesn't have a locator
        # Check for the existence of a locator so that errors when navigating to the course outline page don't show up
        # as errors in the repr method instead.
        return "{}(<browser>, {!r})".format(self.__class__.__name__, self.locator if hasattr(self, 'locator') else None)

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

    def edit_name(self):
        """
        Puts the item's name into editable form.
        """
        self.q(css=self._bounded_selector(self.EDIT_BUTTON_SELECTOR)).first.click()

    def enter_name(self, new_name):
        """
        Enters new_name as the item's display name.
        """
        set_input_value(self, self._bounded_selector(self.NAME_INPUT_SELECTOR), new_name)

    def change_name(self, new_name):
        """
        Changes the container's name.
        """
        self.edit_name()
        set_input_value_and_save(self, self._bounded_selector(self.NAME_INPUT_SELECTOR), new_name)
        self.wait_for_ajax()

    def in_editable_form(self):
        """
        Return whether this outline item's display name is in its editable form.
        """
        return "is-editing" in self.q(
            css=self._bounded_selector(self.NAME_FIELD_WRAPPER_SELECTOR)
        )[0].get_attribute("class")


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
        return self.q(css=child_class.BODY_SELECTOR).map(
            lambda el: child_class(self.browser, el.get_attribute('data-locator'))).results

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
            self._bounded_selector(".add-item a.button-new"),
            require_notification=require_notification,
        )

    def toggle_expand(self):
        """
        Toggle the expansion of this subsection.
        """

        self.browser.execute_script("jQuery.fx.off = true;")

        def subsection_expanded():
            add_button = self.q(css=self._bounded_selector('> .outline-content > .add-item a.button-new')).first.results
            return add_button and add_button[0].is_displayed()

        currently_expanded = subsection_expanded()

        self.q(css=self._bounded_selector('.ui-toggle-expansion i')).first.click()

        EmptyPromise(
            lambda: subsection_expanded() != currently_expanded,
            "Check that the container {} has been toggled".format(self.locator)
        ).fulfill()

        return self

    @property
    def is_collapsed(self):
        """
        Return whether this outline item is currently collapsed.
        """
        return "is-collapsed" in self.q(css=self._bounded_selector('')).first.attrs("class")[0]


class CourseOutlineChild(PageObject, CourseOutlineItem):
    """
    A page object that will be used as a child of :class:`CourseOutlineContainer`.
    """
    def __init__(self, browser, locator):
        super(CourseOutlineChild, self).__init__(browser)
        self.locator = locator

    def is_browser_on_page(self):
        return self.q(css='{}[data-locator="{}"]'.format(self.BODY_SELECTOR, self.locator)).present

    def delete(self, cancel=False):
        """
        Clicks the delete button, then cancels at the confirmation prompt if cancel is True.
        """
        click_css(self, self._bounded_selector('.delete-button'), require_notification=False)
        confirm_prompt(self, cancel)


class CourseOutlineUnit(CourseOutlineChild):
    """
    PageObject that wraps a unit link on the Studio Course Outline page.
    """
    url = None
    BODY_SELECTOR = '.outline-unit'
    NAME_SELECTOR = '.unit-title a'

    def go_to(self):
        """
        Open the container page linked to by this unit link, and return
        an initialized :class:`.ContainerPage` for that unit.
        """
        return ContainerPage(self.browser, self.locator).visit()
    
    def is_browser_on_page(self):
        return self.q(css=self.BODY_SELECTOR).present


class CourseOutlineSubsection(CourseOutlineChild, CourseOutlineContainer):
    """
    :class`.PageObject` that wraps a subsection block on the Studio Course Outline page.
    """
    url = None

    BODY_SELECTOR = '.outline-subsection'
    NAME_SELECTOR = '.subsection-title'
    NAME_FIELD_WRAPPER_SELECTOR = '.subsection-header .wrapper-xblock-field'
    CHILD_CLASS = CourseOutlineUnit

    def unit(self, title):
        """
        Return the :class:`.CourseOutlineUnit with the title `title`.
        """
        return self.child(title)

    def units(self):
        """
        Returns the units in this subsection.
        """
        return self.children()

    def unit_at(self, index):
        """
        Returns the CourseOutlineUnit at the specified index.
        """
        return self.child_at(index)

    def add_unit(self):
        """
        Adds a unit to this subsection
        """
        self.add_child(require_notification=False)


class CourseOutlineSection(CourseOutlineChild, CourseOutlineContainer):
    """
    :class`.PageObject` that wraps a section block on the Studio Course Outline page.
    """
    url = None
    BODY_SELECTOR = '.outline-section'
    NAME_SELECTOR = '.section-title'
    NAME_FIELD_WRAPPER_SELECTOR = '.section-header .wrapper-xblock-field'
    CHILD_CLASS = CourseOutlineSubsection

    def subsection(self, title):
        """
        Return the :class:`.CourseOutlineSubsection` with the title `title`.
        """
        return self.child(title)

    def subsections(self):
        """
        Returns a list of the CourseOutlineSubsections of this section
        """
        return self.children()

    def subsection_at(self, index):
        """
        Returns the CourseOutlineSubsection at the specified index.
        """
        return self.child_at(index)

    def add_subsection(self):
        """
        Adds a subsection to this section
        """
        self.add_child()


class ExpandCollapseLinkState:
    """
    Represents the three states that the expand/collapse link can be in
    """
    MISSING = 0
    COLLAPSE = 1
    EXPAND = 2


class CourseOutlinePage(CoursePage, CourseOutlineContainer):
    """
    Course Outline page in Studio.
    """
    url_path = "course"
    CHILD_CLASS = CourseOutlineSection
    EXPAND_COLLAPSE_CSS = '.button-toggle-expand-collapse'
    BOTTOM_ADD_SECTION_BUTTON = '.outline > .add-section .button-new'

    def is_browser_on_page(self):
        return self.q(css='body.view-outline').present

    def view_live(self):
        """
        Clicks the "View Live" link and switches to the new tab
        """
        click_css(self, '.view-live-button', require_notification=False)
        self.browser.switch_to_window(self.browser.window_handles[-1])

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

    def sections(self):
        """
        Returns the sections of this course outline page.
        """
        return self.children()

    def add_section_from_top_button(self):
        """
        Clicks the button for adding a section which resides at the top of the screen.
        """
        click_css(self, '.wrapper-mast nav.nav-actions .button-new')

    def add_section_from_bottom_button(self):
        """
        Clicks the button for adding a section which resides at the bottom of the screen.
        """
        click_css(self, self.BOTTOM_ADD_SECTION_BUTTON)

    def toggle_expand_collapse(self):
        """
        Toggles whether all sections are expanded or collapsed
        """
        self.q(css=self.EXPAND_COLLAPSE_CSS).click()

    @property
    def bottom_add_section_button(self):
        """
        Returns the query representing the bottom add section button.
        """
        return self.q(css=self.BOTTOM_ADD_SECTION_BUTTON).first

    @property
    def has_no_content_message(self):
        """
        Returns true if a message informing the user that the course has no content is visible
        """
        return self.q(css='.outline .no-content').is_present()

    @property
    def expand_collapse_link_state(self):
        """
        Returns the current state of the expand/collapse link
        """
        link = self.q(css=self.EXPAND_COLLAPSE_CSS)[0]
        if not link.is_displayed():
            return ExpandCollapseLinkState.MISSING
        elif "collapse-all" in link.get_attribute("class"):
            return ExpandCollapseLinkState.COLLAPSE
        else:
            return ExpandCollapseLinkState.EXPAND

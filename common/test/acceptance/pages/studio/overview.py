"""
Course Outline page in Studio.
"""
import datetime

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

from .course_page import CoursePage
from .container import ContainerPage
from .utils import set_input_value_and_save, set_input_value, click_css, confirm_prompt


class CourseOutlineItem(object):
    """
    A mixin class for any :class:`PageObject` shown in a course outline.
    """
    BODY_SELECTOR = None
    EDIT_BUTTON_SELECTOR = '.xblock-field-value-edit'
    NAME_SELECTOR = '.item-title'
    NAME_INPUT_SELECTOR = '.xblock-field-input'
    NAME_FIELD_WRAPPER_SELECTOR = '.xblock-title .wrapper-xblock-field'
    STATUS_MESSAGE_SELECTOR = '> div[class$="status"] .status-message'
    CONFIGURATION_BUTTON_SELECTOR = '.action-item .configure-button'

    def __repr__(self):
        # CourseOutlineItem is also used as a mixin for CourseOutlinePage, which doesn't have a locator
        # Check for the existence of a locator so that errors when navigating to the course outline page don't show up
        # as errors in the repr method instead.
        try:
            return "{}(<browser>, {!r})".format(self.__class__.__name__, self.locator)
        except AttributeError:
            return "{}(<browser>)".format(self.__class__.__name__)

    def _bounded_selector(self, selector):
        """
        Returns `selector`, but limited to this particular `CourseOutlineItem` context
        """
        # If the item doesn't have a body selector or locator, then it can't be bounded
        # This happens in the context of the CourseOutlinePage
        if self.BODY_SELECTOR and hasattr(self, 'locator'):
            return '{}[data-locator="{}"] {}'.format(
                self.BODY_SELECTOR,
                self.locator,
                selector
            )
        else:
            return selector

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

    @property
    def has_status_message(self):
        """
        Returns True if the item has a status message, False otherwise.
        """
        return self.q(css=self._bounded_selector(self.STATUS_MESSAGE_SELECTOR)).first.visible

    @property
    def status_message(self):
        """
        Returns the status message of this item.
        """
        return self.q(css=self._bounded_selector(self.STATUS_MESSAGE_SELECTOR)).text[0]

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

    def finalize_name(self):
        """
        Presses ENTER, saving the value of the display name for this item.
        """
        self.q(css=self._bounded_selector(self.NAME_INPUT_SELECTOR)).results[0].send_keys(Keys.ENTER)
        self.wait_for_ajax()

    def in_editable_form(self):
        """
        Return whether this outline item's display name is in its editable form.
        """
        return "is-editing" in self.q(
            css=self._bounded_selector(self.NAME_FIELD_WRAPPER_SELECTOR)
        )[0].get_attribute("class")

    def edit(self):
        self.q(css=self._bounded_selector(self.CONFIGURATION_BUTTON_SELECTOR)).first.click()
        modal = CourseOutlineModal(self)
        EmptyPromise(lambda: modal.is_shown(), 'Modal is shown.')
        return modal

    @property
    def release_date(self):
        element = self.q(css=self._bounded_selector(".status-release-value"))
        return element.first.text[0] if element.present else None

    @property
    def due_date(self):
        element = self.q(css=self._bounded_selector(".status-grading-date"))
        return element.first.text[0] if element.present else None

    @property
    def policy(self):
        element = self.q(css=self._bounded_selector(".status-grading-value"))
        return element.first.text[0] if element.present else None


class CourseOutlineContainer(CourseOutlineItem):
    """
    A mixin to a CourseOutline page object that adds the ability to load
    a child page object by title or by index.

    CHILD_CLASS must be a :class:`CourseOutlineChild` subclass.
    """
    CHILD_CLASS = None
    ADD_BUTTON_SELECTOR = '> .outline-content > .add-item a.button-new'

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
        return self.q(css=self._bounded_selector(child_class.BODY_SELECTOR)).map(
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
            self._bounded_selector(self.ADD_BUTTON_SELECTOR),
            require_notification=require_notification,
        )

    def toggle_expand(self):
        """
        Toggle the expansion of this subsection.
        """

        self.browser.execute_script("jQuery.fx.off = true;")

        def subsection_expanded():
            add_button = self.q(css=self._bounded_selector(self.ADD_BUTTON_SELECTOR)).first.results
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
        self.q(css=self._bounded_selector(self.ADD_BUTTON_SELECTOR)).click()


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
        return self.q(css='body.view-outline').present and self.q(css='div.ui-loading.is-hidden').present

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


class CourseOutlineModal(object):
    MODAL_SELECTOR = ".edit-outline-item-modal"

    def __init__(self, page):
        self.page = page

    def _bounded_selector(self, selector):
        """
        Returns `selector`, but limited to this particular `CourseOutlineModal` context.
        """
        return " ".join([self.MODAL_SELECTOR, selector])

    def is_shown(self):
        return self.page.q(css=self.MODAL_SELECTOR).present

    def find_css(self, selector):
        return self.page.q(css=self._bounded_selector(selector))

    def click(self, selector, index=0):
        self.find_css(selector).nth(index).click()

    def save(self):
        self.click(".action-save")
        self.page.wait_for_ajax()

    def cancel(self):
        self.click(".action-cancel")

    def has_release_date(self):
        return self.find_css("#start_date").present

    def has_due_date(self):
        return self.find_css("#due_date").present

    def has_policy(self):
        return self.find_css("#grading_type").present

    def set_date(self, property_name, input_selector, date):
        """
        Set `date` value to input pointed by `selector` and `property_name`.
        """
        month, day, year = map(int, date.split('/'))
        self.click(input_selector)
        if getattr(self, property_name):
            current_month, current_year = map(int, getattr(self, property_name).split('/')[1:])
        else:  # Use default timepicker values, which are current month and year.
            current_month, current_year = datetime.datetime.today().month, datetime.datetime.today().year
        date_diff = 12 * (year - current_year) + month - current_month
        selector = "a.ui-datepicker-{}".format('next' if date_diff > 0 else 'prev')
        for i in xrange(abs(date_diff)):
            self.page.q(css=selector).click()
        self.page.q(css="a.ui-state-default").nth(day - 1).click()  # set day
        EmptyPromise(
            lambda: getattr(self, property_name) == u'{m}/{d}/{y}'.format(m=month, d=day, y=year),
            "{} is updated in modal.".format(property_name)
        ).fulfill()

    @property
    def release_date(self):
        return self.find_css("#start_date").first.attrs('value')[0]

    @release_date.setter
    def release_date(self, date):
        """
        Date is "mm/dd/yyyy" string.
        """
        self.set_date('release_date', "#start_date", date)

    @property
    def due_date(self):
        return self.find_css("#due_date").first.attrs('value')[0]

    @due_date.setter
    def due_date(self, date):
        """
        Date is "mm/dd/yyyy" string.
        """
        self.set_date('due_date', "#due_date", date)

    @property
    def policy(self):
        """
        Select the grading format with `value` in the drop-down list.
        """
        element = self.find_css('#grading_type')[0]
        return self.get_selected_option_text(element)

    @policy.setter
    def policy(self, grading_label):
        """
        Select the grading format with `value` in the drop-down list.
        """
        element = self.find_css('#grading_type')[0]
        select = Select(element)
        select.select_by_visible_text(grading_label)

        EmptyPromise(
            lambda: self.policy == grading_label,
            "Grading label is updated.",
        ).fulfill()

    def get_selected_option_text(self, element):
        """
        Returns the text of the first selected option for the element.
        """
        if element:
            select = Select(element)
            return select.first_selected_option.text
        else:
            return None

"""
Course Outline page in Studio.
"""
import datetime

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

from common.test.acceptance.pages.common.utils import click_css, confirm_prompt

from common.test.acceptance.pages.studio.course_page import CoursePage
from common.test.acceptance.pages.studio.container import ContainerPage
from common.test.acceptance.pages.studio.utils import set_input_value_and_save, set_input_value


class CourseOutlineItem(object):
    """
    A mixin class for any :class:`PageObject` shown in a course outline.
    """
    # Note there are a few pylint disable=no-member occurances in this class, because
    # it was written assuming it is going to be a mixin to a PageObject and will have functions
    # such as self.wait_for_ajax, which doesn't exist on a generic `object`.
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
            return "{}(<browser>, {!r})".format(self.__class__.__name__, self.locator)  # pylint: disable=no-member
        except AttributeError:
            return "{}(<browser>)".format(self.__class__.__name__)

    def _bounded_selector(self, selector):
        """
        Returns `selector`, but limited to this particular `CourseOutlineItem` context
        """
        # If the item doesn't have a body selector or locator, then it can't be bounded
        # This happens in the context of the CourseOutlinePage
        # pylint: disable=no-member
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
        name_element = self.q(css=self._bounded_selector(self.NAME_SELECTOR)).first  # pylint: disable=no-member
        if name_element:
            return name_element.text[0]
        else:
            return None

    @property
    def has_status_message(self):
        """
        Returns True if the item has a status message, False otherwise.
        """
        return self.q(css=self._bounded_selector(self.STATUS_MESSAGE_SELECTOR)).first.visible  # pylint: disable=no-member

    @property
    def status_message(self):
        """
        Returns the status message of this item.
        """
        return self.q(css=self._bounded_selector(self.STATUS_MESSAGE_SELECTOR)).text[0]  # pylint: disable=no-member

    @property
    def has_staff_lock_warning(self):
        """ Returns True if the 'Contains staff only content' message is visible """
        return self.status_message == 'Contains staff only content' if self.has_status_message else False

    @property
    def is_staff_only(self):
        """ Returns True if the visiblity state of this item is staff only (has a black sidebar) """
        return "is-staff-only" in self.q(css=self._bounded_selector(''))[0].get_attribute("class")  # pylint: disable=no-member

    def edit_name(self):
        """
        Puts the item's name into editable form.
        """
        self.q(css=self._bounded_selector(self.EDIT_BUTTON_SELECTOR)).first.click()  # pylint: disable=no-member

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
        self.wait_for_ajax()  # pylint: disable=no-member

    def finalize_name(self):
        """
        Presses ENTER, saving the value of the display name for this item.
        """
        # pylint: disable=no-member
        self.q(css=self._bounded_selector(self.NAME_INPUT_SELECTOR)).results[0].send_keys(Keys.ENTER)
        self.wait_for_ajax()

    def set_staff_lock(self, is_locked):
        """
        Sets the explicit staff lock of item on the container page to is_locked.
        """
        modal = self.edit()
        modal.is_explicitly_locked = is_locked
        modal.save()

    def in_editable_form(self):
        """
        Return whether this outline item's display name is in its editable form.
        """
        # pylint: disable=no-member
        return "is-editing" in self.q(
            css=self._bounded_selector(self.NAME_FIELD_WRAPPER_SELECTOR)
        )[0].get_attribute("class")

    def edit(self):
        """
        Puts the item into editable form.
        """
        self.q(css=self._bounded_selector(self.CONFIGURATION_BUTTON_SELECTOR)).first.click()  # pylint: disable=no-member
        modal = CourseOutlineModal(self)
        EmptyPromise(lambda: modal.is_shown(), 'Modal is shown.')  # pylint: disable=unnecessary-lambda
        return modal

    @property
    def release_date(self):
        """
        Returns the release date from the page. Date is "mm/dd/yyyy" string.
        """
        element = self.q(css=self._bounded_selector(".status-release-value"))  # pylint: disable=no-member
        return element.first.text[0] if element.present else None

    @property
    def due_date(self):
        """
        Returns the due date from the page. Date is "mm/dd/yyyy" string.
        """
        element = self.q(css=self._bounded_selector(".status-grading-date"))  # pylint: disable=no-member
        return element.first.text[0] if element.present else None

    @property
    def policy(self):
        """
        Select the grading format with `value` in the drop-down list.
        """
        element = self.q(css=self._bounded_selector(".status-grading-value"))  # pylint: disable=no-member
        return element.first.text[0] if element.present else None

    def publish(self):
        """
        Publish the unit.
        """
        click_css(self, self._bounded_selector('.action-publish'), require_notification=False)
        modal = CourseOutlineModal(self)
        EmptyPromise(lambda: modal.is_shown(), 'Modal is shown.')  # pylint: disable=unnecessary-lambda
        modal.publish()

    @property
    def publish_action(self):
        """
        Returns the link for publishing a unit.
        """
        return self.q(css=self._bounded_selector('.action-publish')).first  # pylint: disable=no-member


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

        # pylint: disable=no-member
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
        # pylint: disable=no-member
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

    def expand_subsection(self):
        """
        Toggle the expansion of this subsection.
        """
        # pylint: disable=no-member
        self.browser.execute_script("jQuery.fx.off = true;")

        def subsection_expanded():
            """
            Returns whether or not this subsection is expanded.
            """
            self.wait_for_element_presence(
                self._bounded_selector(self.ADD_BUTTON_SELECTOR), 'Toggle control is present'
            )
            add_button = self.q(css=self._bounded_selector(self.ADD_BUTTON_SELECTOR)).first.results
            return add_button and add_button[0].is_displayed()

        currently_expanded = subsection_expanded()

        # Need to click slightly off-center in order for the click to be recognized.
        ele = self.browser.find_element_by_css_selector(self._bounded_selector('.ui-toggle-expansion .fa'))
        ActionChains(self.browser).move_to_element_with_offset(ele, 4, 4).click().perform()
        self.wait_for_element_presence(self._bounded_selector(self.ADD_BUTTON_SELECTOR), 'Subsection is expanded')

        EmptyPromise(
            lambda: subsection_expanded() != currently_expanded,
            "Check that the container {} has been toggled".format(self.locator)
        ).fulfill()

        self.browser.execute_script("jQuery.fx.off = false;")

        return self

    @property
    def is_collapsed(self):
        """
        Return whether this outline item is currently collapsed.
        """
        return "is-collapsed" in self.q(css=self._bounded_selector('')).first.attrs("class")[0]  # pylint: disable=no-member


class CourseOutlineChild(PageObject, CourseOutlineItem):
    """
    A page object that will be used as a child of :class:`CourseOutlineContainer`.
    """
    url = None
    BODY_SELECTOR = '.outline-item'

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
    def children(self):
        """
        Will return any first-generation descendant items of this item.
        """
        descendants = self.q(css=self._bounded_selector(self.BODY_SELECTOR)).map(
            lambda el: CourseOutlineChild(self.browser, el.get_attribute('data-locator'))).results

        # Now remove any non-direct descendants.
        grandkids = []
        for descendant in descendants:
            grandkids.extend(descendant.children)

        grand_locators = [grandkid.locator for grandkid in grandkids]
        return [descendant for descendant in descendants if descendant.locator not in grand_locators]


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

    def children(self):
        return self.q(css=self._bounded_selector(self.BODY_SELECTOR)).map(
            lambda el: CourseOutlineUnit(self.browser, el.get_attribute('data-locator'))).results


class CourseOutlineSubsection(CourseOutlineContainer, CourseOutlineChild):
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


class CourseOutlineSection(CourseOutlineContainer, CourseOutlineChild):
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


class ExpandCollapseLinkState(object):
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
        return all([
            self.q(css='body.view-outline').present,
            self.q(css='.content-primary').present,
            self.q(css='div.ui-loading.is-hidden').present
        ])

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

    def add_section_from_bottom_button(self, click_child_icon=False):
        """
        Clicks the button for adding a section which resides at the bottom of the screen.
        """
        element_css = self.BOTTOM_ADD_SECTION_BUTTON
        if click_child_icon:
            element_css += " .fa-plus"

        click_css(self, element_css)

    def toggle_expand_collapse(self):
        """
        Toggles whether all sections are expanded or collapsed
        """
        self.q(css=self.EXPAND_COLLAPSE_CSS).click()

    def start_reindex(self):
        """
        Starts course reindex by clicking reindex button
        """
        self.reindex_button.click()

    def open_subsection_settings_dialog(self, index=0):
        """
        clicks on the settings button of subsection.
        """
        self.q(css=".subsection-header-actions .configure-button").nth(index).click()
        self.wait_for_element_presence('.course-outline-modal', 'Subsection settings modal is present.')

    def change_problem_release_date(self):
        """
        Sets a new start date
        """
        self.q(css=".subsection-header-actions .configure-button").first.click()
        self.q(css="#start_date").fill("01/01/2030")
        self.q(css=".action-save").first.click()
        self.wait_for_ajax()

    def change_problem_due_date(self, date):
        """
        Sets a new due date.

        Expects date to be a string that will be accepted by the input (for example, '01/01/1970')
        """
        self.q(css=".subsection-header-actions .configure-button").first.click()
        self.q(css="#due_date").fill(date)
        self.q(css=".action-save").first.click()
        self.wait_for_ajax()

    def select_advanced_tab(self, desired_item='special_exam'):
        """
        Select the advanced settings tab
        """
        self.q(css=".settings-tab-button[data-tab='advanced']").first.click()
        if desired_item == 'special_exam':
            self.wait_for_element_presence('input.no_special_exam', 'Special exam settings fields not present.')
        if desired_item == 'gated_content':
            self.wait_for_element_visibility('#is_prereq', 'Gating settings fields are present.')

    def make_exam_proctored(self):
        """
        Makes a Proctored exam.
        """
        self.q(css="input.proctored_exam").first.click()
        self.q(css=".action-save").first.click()
        self.wait_for_ajax()

    def make_exam_timed(self, hide_after_due=False):
        """
        Makes a timed exam.
        """
        self.q(css="input.timed_exam").first.click()
        if hide_after_due:
            self.q(css='input[name=content-visibility][value=hide_after_due]').first.click()
        self.q(css=".action-save").first.click()
        self.wait_for_ajax()

    def select_none_exam(self):
        """
        Choose "none" exam but do not press enter
        """
        self.q(css="input.no_special_exam").first.click()

    def select_timed_exam(self):
        """
        Choose a timed exam but do not press enter
        """
        self.q(css="input.timed_exam").first.click()

    def select_proctored_exam(self):
        """
        Choose a proctored exam but do not press enter
        """
        self.q(css="input.proctored_exam").first.click()

    def select_practice_exam(self):
        """
        Choose a practice exam but do not press enter
        """
        self.q(css="input.practice_exam").first.click()

    def time_allotted_field_visible(self):
        """
        returns whether the time allotted field is visible
        """
        return self.q(css=".field-time-limit").visible

    def exam_review_rules_field_visible(self):
        """
        Returns whether the review rules field is visible
        """
        return self.q(css=".field-exam-review-rules").visible

    def proctoring_items_are_displayed(self):
        """
        Returns True if all the items are found.
        """

        # The None radio button
        if not self.q(css="input.no_special_exam").present:
            return False

        # The Timed exam radio button
        if not self.q(css="input.timed_exam").present:
            return False

        # The Proctored exam radio button
        if not self.q(css="input.proctored_exam").present:
            return False

        # The Practice exam radio button
        if not self.q(css="input.practice_exam").present:
            return False

        return True

    def make_gating_prerequisite(self):
        """
        Makes a subsection a gating prerequisite.
        """
        if not self.q(css="#is_prereq")[0].is_selected():
            self.q(css='label[for="is_prereq"]').click()
        self.q(css=".action-save").first.click()
        self.wait_for_ajax()

    def add_prerequisite_to_subsection(self, min_score):
        """
        Adds a prerequisite to a subsection.
        """
        Select(self.q(css="#prereq")[0]).select_by_index(1)
        self.q(css="#prereq_min_score").fill(min_score)
        self.q(css=".action-save").first.click()
        self.wait_for_ajax()

    def gating_prerequisite_checkbox_is_visible(self):
        """
        Returns True if the gating prerequisite checkbox is visible.
        """

        # The Prerequisite checkbox is visible
        return self.q(css="#is_prereq").visible

    def gating_prerequisite_checkbox_is_checked(self):
        """
        Returns True if the gating prerequisite checkbox is checked.
        """

        # The Prerequisite checkbox is checked
        return self.q(css="#is_prereq:checked").present

    def gating_prerequisites_dropdown_is_visible(self):
        """
        Returns True if the gating prerequisites dropdown is visible.
        """

        # The Prerequisites dropdown is visible
        return self.q(css="#prereq").visible

    def gating_prerequisite_min_score_is_visible(self):
        """
        Returns True if the gating prerequisite minimum score input is visible.
        """

        # The Prerequisites dropdown is visible
        return self.q(css="#prereq_min_score").visible

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
    def has_rerun_notification(self):
        """
        Returns true iff the rerun notification is present on the page.
        """
        return self.q(css='.wrapper-alert.is-shown').is_present()

    def dismiss_rerun_notification(self):
        """
        Clicks the dismiss button in the rerun notification.
        """
        self.q(css='.dismiss-button').click()

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

    @property
    def reindex_button(self):
        """
        Returns reindex button.
        """
        return self.q(css=".button.button-reindex")[0]

    def expand_all_subsections(self):
        """
        Expands all the subsections in this course.
        """
        for section in self.sections():
            if section.is_collapsed:
                section.expand_subsection()
            for subsection in section.subsections():
                if subsection.is_collapsed:
                    subsection.expand_subsection()

    @property
    def xblocks(self):
        """
        Return a list of xblocks loaded on the outline page.
        """
        return self.children(CourseOutlineChild)

    @property
    def license(self):
        """
        Returns the course license text, if present. Else returns None.
        """
        return self.q(css=".license-value").first.text[0]

    @property
    def deprecated_warning_visible(self):
        """
        Returns true if the deprecated warning is visible.
        """
        return self.q(css='.wrapper-alert-error.is-shown').is_present()

    @property
    def warning_heading_text(self):
        """
        Returns deprecated warning heading text.
        """
        return self.q(css='.warning-heading-text').text[0]

    @property
    def components_list_heading(self):
        """
        Returns deprecated warning component list heading text.
        """
        return self.q(css='.components-list-heading-text').text[0]

    @property
    def modules_remove_text_shown(self):
        """
        Returns True if deprecated warning advance modules remove text is visible.
        """
        return self.q(css='.advance-modules-remove-text').visible

    @property
    def modules_remove_text(self):
        """
        Returns deprecated warning advance modules remove text.
        """
        return self.q(css='.advance-modules-remove-text').text[0]

    @property
    def components_visible(self):
        """
        Returns True if components list visible.
        """
        return self.q(css='.components-list').visible

    @property
    def components_display_names(self):
        """
        Returns deprecated warning components display name list.
        """
        return self.q(css='.components-list li>a').text

    @property
    def deprecated_advance_modules(self):
        """
        Returns deprecated advance modules list.
        """
        return self.q(css='.advance-modules-list li').text


class CourseOutlineModal(object):
    """
    Page object specifically for a modal window on the course outline page.
    """
    MODAL_SELECTOR = ".wrapper-modal-window"

    def __init__(self, page):
        self.page = page

    def _bounded_selector(self, selector):
        """
        Returns `selector`, but limited to this particular `CourseOutlineModal` context.
        """
        return " ".join([self.MODAL_SELECTOR, selector])

    def is_shown(self):
        """
        Return whether or not the modal defined by self.MODAL_SELECTOR is shown.
        """
        return self.page.q(css=self.MODAL_SELECTOR).present

    def find_css(self, selector):
        """
        Find the given css selector on the page.
        """
        return self.page.q(css=self._bounded_selector(selector))

    def click(self, selector, index=0):
        """
        Perform a Click action on the given selector.
        """
        self.find_css(selector).nth(index).click()

    def save(self):
        """
        Click the save action button, and wait for the ajax call to return.
        """
        self.click(".action-save")
        self.page.wait_for_ajax()

    def publish(self):
        """
        Click the publish action button, and wait for the ajax call to return.
        """
        self.click(".action-publish")
        self.page.wait_for_ajax()

    def cancel(self):
        """
        Click the cancel action button.
        """
        self.click(".action-cancel")

    def has_release_date(self):
        """
        Check if the input box for the release date exists in the subsection's settings window
        """
        return self.find_css("#start_date").present

    def has_release_time(self):
        """
        Check if the input box for the release time exists in the subsection's settings window
        """
        return self.find_css("#start_time").present

    def has_due_date(self):
        """
        Check if the input box for the due date exists in the subsection's settings window
        """
        return self.find_css("#due_date").present

    def has_due_time(self):
        """
        Check if the input box for the due time exists in the subsection's settings window
        """
        return self.find_css("#due_time").present

    def has_policy(self):
        """
        Check if the input for the  grading policy is present.
        """
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
        for __ in xrange(abs(date_diff)):
            self.page.q(css=selector).click()
        self.page.q(css="a.ui-state-default").nth(day - 1).click()  # set day
        self.page.wait_for_element_invisibility("#ui-datepicker-div", "datepicker should be closed")
        EmptyPromise(
            lambda: getattr(self, property_name) == u'{m}/{d}/{y}'.format(m=month, d=day, y=year),
            "{} is updated in modal.".format(property_name)
        ).fulfill()

    def set_time(self, input_selector, time):
        """
        Set `time` value to input pointed by `input_selector`
        Not using the time picker to make sure it's not being rounded up
        """

        self.page.q(css=input_selector).fill(time)
        self.page.q(css=input_selector).results[0].send_keys(Keys.ENTER)

    @property
    def release_date(self):
        """
        Returns the unit's release date. Date is "mm/dd/yyyy" string.
        """
        return self.find_css("#start_date").first.attrs('value')[0]

    @release_date.setter
    def release_date(self, date):
        """
        Sets the unit's release date to `date`. Date is "mm/dd/yyyy" string.
        """
        self.set_date('release_date', "#start_date", date)

    @property
    def release_time(self):
        """
        Returns the current value of the release time. Default is u'00:00'
        """
        return self.find_css("#start_time").first.attrs('value')[0]

    @release_time.setter
    def release_time(self, time):
        """
        Time is "HH:MM" string.
        """
        self.set_time("#start_time", time)

    @property
    def due_date(self):
        """
        Returns the due date from the page. Date is "mm/dd/yyyy" string.
        """
        return self.find_css("#due_date").first.attrs('value')[0]

    @due_date.setter
    def due_date(self, date):
        """
        Sets the due date for the unit. Date is "mm/dd/yyyy" string.
        """
        self.set_date('due_date', "#due_date", date)

    @property
    def due_time(self):
        """
        Returns the current value of the release time. Default is u''
        """
        return self.find_css("#due_time").first.attrs('value')[0]

    @due_time.setter
    def due_time(self, time):
        """
        Time is "HH:MM" string.
        """
        self.set_time("#due_time", time)

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

    @property
    def is_staff_lock_visible(self):
        """
        Returns true if the staff lock option is visible, either as a checkbox
        (section and unit levels) or a radio button (subsection level).
        """
        return self.find_css('#staff_lock').visible or self.find_css('input[name=content-visibility]').visible

    def ensure_staff_lock_visible(self):
        """
        Ensures the staff lock option is visible, clicking on the advanced tab
        if needed.
        """
        if not self.is_staff_lock_visible:
            self.find_css(".settings-tab-button[data-tab=advanced]").click()

    @property
    def is_explicitly_locked(self):
        """
        Returns true if the explict staff lock checkbox is checked, false otherwise.
        """
        self.ensure_staff_lock_visible()
        if self.find_css('input[name=content-visibility]').visible:
            return self.find_css('input[name=content-visibility][value=staff_only]')[0].is_selected()
        else:
            return self.find_css('#staff_lock')[0].is_selected()

    @is_explicitly_locked.setter
    def is_explicitly_locked(self, value):
        """
        Checks the explicit staff lock box if value is true, otherwise selects "visible".
        """
        self.ensure_staff_lock_visible()
        if self.find_css('#staff_lock').visible:
            # Section or unit level - select checkbox as needed
            if value != self.is_explicitly_locked:
                self.find_css('label[for="staff_lock"]').click()
        else:
            # Subsection level - select correct radio button
            if value:
                self.find_css('input[name=content-visibility][value=staff_only]').click()
            else:
                self.find_css('input[name=content-visibility][value=visible]').click()
        EmptyPromise(lambda: value == self.is_explicitly_locked, "Explicit staff lock is updated").fulfill()

    def shows_staff_lock_warning(self):
        """
        Returns true iff the staff lock warning is visible.
        """
        return self.find_css('.staff-lock .tip-warning').visible

    def get_selected_option_text(self, element):
        """
        Returns the text of the first selected option for the element.
        """
        if element:
            select = Select(element)
            return select.first_selected_option.text
        else:
            return None

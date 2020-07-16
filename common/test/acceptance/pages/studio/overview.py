"""
Course Outline page in Studio.
"""


from bok_choy.javascript import js_defined, wait_for_js
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise
from selenium.webdriver.support.ui import Select

from common.test.acceptance.pages.studio.container import ContainerPage
from common.test.acceptance.pages.studio.course_page import CoursePage


@js_defined('jQuery')
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
    STATUS_MESSAGE_SELECTOR = '> div[class$="-status"] .status-messages'
    CONFIGURATION_BUTTON_SELECTOR = '.action-item .configure-button'

    def __repr__(self):
        # CourseOutlineItem is also used as a mixin for CourseOutlinePage, which doesn't have a locator
        # Check for the existence of a locator so that errors when navigating to the course outline page don't show up
        # as errors in the repr method instead.
        try:
            return u"{}(<browser>, {!r})".format(self.__class__.__name__, self.locator)
        except AttributeError:
            return u"{}(<browser>)".format(self.__class__.__name__)

    def _bounded_selector(self, selector):
        """
        Returns `selector`, but limited to this particular `CourseOutlineItem` context
        """
        # If the item doesn't have a body selector or locator, then it can't be bounded
        # This happens in the context of the CourseOutlinePage
        # pylint: disable=no-member
        if self.BODY_SELECTOR and hasattr(self, 'locator'):
            return u'{}[data-locator="{}"] {}'.format(
                self.BODY_SELECTOR,
                self.locator,
                selector
            )
        else:
            return selector

    def edit(self):
        """
        Puts the item into editable form.
        """
        self.q(css=self._bounded_selector(self.CONFIGURATION_BUTTON_SELECTOR)).first.click()  # pylint: disable=no-member
        if 'subsection' in self.BODY_SELECTOR:
            modal = SubsectionOutlineModal(self)
        else:
            modal = CourseOutlineModal(self)
        EmptyPromise(lambda: modal.is_shown(), 'Modal is shown.')  # pylint: disable=unnecessary-lambda
        return modal


class CourseOutlineContainer(CourseOutlineItem):
    """
    A mixin to a CourseOutline page object that adds the ability to load
    a child page object by title or by index.

    CHILD_CLASS must be a :class:`CourseOutlineChild` subclass.
    """
    CHILD_CLASS = None
    ADD_BUTTON_SELECTOR = '> .outline-content > .add-item a.button-new'

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

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to this particular `CourseOutlineChild` context
        """
        return u'{}[data-locator="{}"] {}'.format(
            self.BODY_SELECTOR,
            self.locator,
            selector
        )


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

    def section_at(self, index):
        """
        Returns the :class:`.CourseOutlineSection` at the specified index.
        """
        return self.child_at(index)

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

    def select_advanced_tab(self, desired_item='special_exam'):
        """
        Select the advanced settings tab
        """
        self.q(css=".settings-tab-button[data-tab='advanced']").first.click()
        if desired_item == 'special_exam':
            self.wait_for_element_presence('input.no_special_exam', 'Special exam settings fields not present.')
        if desired_item == 'gated_content':
            self.wait_for_element_visibility('#is_prereq', 'Gating settings fields are present.')


class CourseOutlineModal(object):
    """
    Page object specifically for a modal window on the course outline page.

    Subsections are handled slightly differently in some regards, and should use SubsectionOutlineModal.
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


class SubsectionOutlineModal(CourseOutlineModal):
    """
    Subclass to handle a few special cases with subsection modals.
    """

    @property
    def is_explicitly_locked(self):
        """
        Override - returns True if staff_only is set.
        """
        return self.subsection_visibility == 'staff_only'

    @property
    def subsection_visibility(self):
        """
        Returns the current visibility setting for a subsection
        """
        self.ensure_staff_lock_visible()
        return self.find_css('input[name=content-visibility]:checked').first.attrs('value')[0]

    @is_explicitly_locked.setter
    def is_explicitly_locked(self, value):
        """
        Override - sets visibility to staff_only if True, else 'visible'.

        For hide_after_due, use the set_subsection_visibility method directly.
        """
        self.subsection_visibility = 'staff_only' if value else 'visible'

    @subsection_visibility.setter
    def subsection_visibility(self, value):
        """
        Sets the subsection visibility to the given value.
        """
        self.ensure_staff_lock_visible()
        self.find_css('input[name=content-visibility][value=' + value + ']').click()
        EmptyPromise(lambda: value == self.subsection_visibility, "Subsection visibility is updated").fulfill()

    @property
    def is_staff_lock_visible(self):
        """
        Override - Returns true if the staff lock option is visible.
        """
        return self.find_css('input[name=content-visibility]').visible

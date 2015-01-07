"""
Library edit page in Studio
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from .overview import CourseOutlineModal
from .container import XBlockWrapper
from ...pages.studio.pagination import PaginatedMixin
from ...tests.helpers import disable_animations
from .utils import confirm_prompt, wait_for_notification
from . import BASE_URL


class LibraryPage(PageObject, PaginatedMixin):
    """
    Library page in Studio
    """

    def __init__(self, browser, locator):
        super(LibraryPage, self).__init__(browser)
        self.locator = locator

    @property
    def url(self):
        """
        URL to the library edit page for the given library.
        """
        return "{}/library/{}".format(BASE_URL, unicode(self.locator))

    def is_browser_on_page(self):
        """
        Returns True iff the browser has loaded the library edit page.
        """
        return self.q(css='body.view-library').present

    def get_header_title(self):
        """
        The text of the main heading (H1) visible on the page.
        """
        return self.q(css='h1.page-header-title').text

    def wait_until_ready(self):
        """
        When the page first loads, there is a loading indicator and most
        functionality is not yet available. This waits for that loading to
        finish.

        Always call this before using the page. It also disables animations
        for improved test reliability.
        """
        self.wait_for_ajax()
        self.wait_for_element_invisibility(
            '.ui-loading',
            'Wait for the page to complete its initial loading of XBlocks via AJAX'
        )
        disable_animations(self)

    @property
    def xblocks(self):
        """
        Return a list of xblocks loaded on the container page.
        """
        return self._get_xblocks()

    def click_duplicate_button(self, xblock_id):
        """
        Click on the duplicate button for the given XBlock
        """
        self._action_btn_for_xblock_id(xblock_id, "duplicate").click()
        wait_for_notification(self)
        self.wait_for_ajax()

    def click_delete_button(self, xblock_id, confirm=True):
        """
        Click on the delete button for the given XBlock
        """
        self._action_btn_for_xblock_id(xblock_id, "delete").click()
        if confirm:
            confirm_prompt(self)  # this will also wait_for_notification()
            self.wait_for_ajax()

    def _get_xblocks(self):
        """
        Create an XBlockWrapper for each XBlock div found on the page.
        """
        prefix = '.wrapper-xblock.level-page '
        return self.q(css=prefix + XBlockWrapper.BODY_SELECTOR).map(
            lambda el: XBlockWrapper(self.browser, el.get_attribute('data-locator'))
        ).results

    def _div_for_xblock_id(self, xblock_id):
        """
        Given an XBlock's usage locator as a string, return the WebElement for
        that block's wrapper div.
        """
        return self.q(css='.wrapper-xblock.level-page .studio-xblock-wrapper').filter(
            lambda el: el.get_attribute('data-locator') == xblock_id
        )

    def _action_btn_for_xblock_id(self, xblock_id, action):
        """
        Given an XBlock's usage locator as a string, return one of its action
        buttons.
        action is 'edit', 'duplicate', or 'delete'
        """
        return self._div_for_xblock_id(xblock_id)[0].find_element_by_css_selector(
            '.header-actions .{action}-button.action-button'.format(action=action)
        )


class StudioLibraryContentXBlockEditModal(CourseOutlineModal, PageObject):
    """
    Library Content XBlock Modal edit window
    """
    url = None
    MODAL_SELECTOR = ".wrapper-modal-window-edit-xblock"

    # Labels used to identify the fields on the edit modal:
    LIBRARY_LABEL = "Libraries"
    COUNT_LABEL = "Count"
    SCORED_LABEL = "Scored"
    PROBLEM_TYPE_LABEL = "Problem Type"

    def is_browser_on_page(self):
        """
        Check that we are on the right page in the browser.
        """
        return self.is_shown()

    @property
    def library_key(self):
        """
        Gets value of first library key input
        """
        library_key_input = self.get_metadata_input(self.LIBRARY_LABEL)
        if library_key_input is not None:
            return library_key_input.get_attribute('value').strip(',')
        return None

    @library_key.setter
    def library_key(self, library_key):
        """
        Sets value of first library key input, creating it if necessary
        """
        library_key_input = self.get_metadata_input(self.LIBRARY_LABEL)
        if library_key_input is None:
            library_key_input = self._add_library_key()
        if library_key is not None:
            # can't use lib_text.clear() here as input get deleted by client side script
            library_key_input.send_keys(Keys.HOME)
            library_key_input.send_keys(Keys.SHIFT, Keys.END)
            library_key_input.send_keys(library_key)
        else:
            library_key_input.clear()
        EmptyPromise(lambda: self.library_key == library_key, "library_key is updated in modal.").fulfill()

    @property
    def count(self):
        """
        Gets value of children count input
        """
        return int(self.get_metadata_input(self.COUNT_LABEL).get_attribute('value'))

    @count.setter
    def count(self, count):
        """
        Sets value of children count input
        """
        count_text = self.get_metadata_input(self.COUNT_LABEL)
        count_text.clear()
        count_text.send_keys(count)
        EmptyPromise(lambda: self.count == count, "count is updated in modal.").fulfill()

    @property
    def scored(self):
        """
        Gets value of scored select
        """
        value = self.get_metadata_input(self.SCORED_LABEL).get_attribute('value')
        if value == 'True':
            return True
        elif value == 'False':
            return False
        raise ValueError("Unknown value {value} set for {label}".format(value=value, label=self.SCORED_LABEL))

    @scored.setter
    def scored(self, scored):
        """
        Sets value of scored select
        """
        select_element = self.get_metadata_input(self.SCORED_LABEL)
        select_element.click()
        scored_select = Select(select_element)
        scored_select.select_by_value(str(scored))
        EmptyPromise(lambda: self.scored == scored, "scored is updated in modal.").fulfill()

    @property
    def capa_type(self):
        """
        Gets value of CAPA type select
        """
        return self.get_metadata_input(self.PROBLEM_TYPE_LABEL).get_attribute('value')

    @capa_type.setter
    def capa_type(self, value):
        """
        Sets value of CAPA type select
        """
        select_element = self.get_metadata_input(self.PROBLEM_TYPE_LABEL)
        select_element.click()
        problem_type_select = Select(select_element)
        problem_type_select.select_by_value(value)
        EmptyPromise(lambda: self.capa_type == value, "problem type is updated in modal.").fulfill()

    def _add_library_key(self):
        """
        Adds library key input
        """
        wrapper = self._get_metadata_element(self.LIBRARY_LABEL)
        add_button = wrapper.find_element_by_xpath(".//a[contains(@class, 'create-action')]")
        add_button.click()
        return self._get_list_inputs(wrapper)[0]

    def _get_list_inputs(self, list_wrapper):
        """
        Finds nested input elements (useful for List and Dict fields)
        """
        return list_wrapper.find_elements_by_xpath(".//input[@type='text']")

    def _get_metadata_element(self, metadata_key):
        """
        Gets metadata input element (a wrapper div for List and Dict fields)
        """
        metadata_inputs = self.find_css(".metadata_entry .wrapper-comp-setting label.setting-label")
        target_label = [elem for elem in metadata_inputs if elem.text == metadata_key][0]
        label_for = target_label.get_attribute('for')
        return self.find_css("#" + label_for)[0]

    def get_metadata_input(self, metadata_key):
        """
        Gets input/select element for given field
        """
        element = self._get_metadata_element(metadata_key)
        if element.tag_name == 'div':
            # List or Dict field - return first input
            # TODO support multiple values
            inputs = self._get_list_inputs(element)
            element = inputs[0] if inputs else None
        return element


class StudioLibraryContainerXBlockWrapper(XBlockWrapper):
    """
    Wraps :class:`.container.XBlockWrapper` for use with LibraryContent blocks
    """
    url = None

    @classmethod
    def from_xblock_wrapper(cls, xblock_wrapper):
        """
        Factory method: creates :class:`.StudioLibraryContainerXBlockWrapper` from :class:`.container.XBlockWrapper`
        """
        return cls(xblock_wrapper.browser, xblock_wrapper.locator)

    def get_body_paragraphs(self):
        """
        Gets library content body paragraphs
        """
        return self.q(css=self._bounded_selector(".xblock-message-area p"))

    def refresh_children(self):
        """
        Click "Update now..." button
        """
        btn_selector = self._bounded_selector(".library-update-btn")
        refresh_button = self.q(css=btn_selector)
        refresh_button.click()
        self.wait_for_element_absence(btn_selector, 'Wait for the XBlock to reload')

"""
Library edit page in Studio
"""
from bok_choy.javascript import js_defined, wait_for_js
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise
from selenium.webdriver.support.select import Select
from common.test.acceptance.pages.studio.component_editor import ComponentEditorView
from common.test.acceptance.pages.studio.container import XBlockWrapper
from common.test.acceptance.pages.studio.users import UsersPageMixin
from common.test.acceptance.pages.studio.pagination import PaginatedMixin
from selenium.webdriver.common.keys import Keys

from common.test.acceptance.pages.common.utils import confirm_prompt, wait_for_notification

from common.test.acceptance.pages.studio import BASE_URL


class LibraryPage(PageObject):
    """
    Base page for Library pages. Defaults URL to the edit page.
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


class LibraryEditPage(LibraryPage, PaginatedMixin, UsersPageMixin):
    """
    Library edit page in Studio
    """

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
        super(LibraryEditPage, self).wait_until_ready()

    @property
    def xblocks(self):
        """
        Return a list of xblocks loaded on the container page.
        """
        return self._get_xblocks()

    def are_previews_showing(self):
        """
        Determines whether or not previews are showing for XBlocks
        """
        return all([not xblock.is_placeholder() for xblock in self.xblocks])

    def toggle_previews(self):
        """
        Clicks the preview toggling button and waits for the previews to appear or disappear.
        """
        toggle = not self.are_previews_showing()
        self.q(css='.toggle-preview-button').click()
        EmptyPromise(
            lambda: self.are_previews_showing() == toggle,
            'Preview is visible: %s' % toggle,
            timeout=30
        ).fulfill()
        self.wait_until_ready()

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


class StudioLibraryContentEditor(ComponentEditorView):
    """
    Library Content XBlock Modal edit window
    """
    # Labels used to identify the fields on the edit modal:
    LIBRARY_LABEL = "Library"
    COUNT_LABEL = "Count"
    SCORED_LABEL = "Scored"
    PROBLEM_TYPE_LABEL = "Problem Type"

    @property
    def library_name(self):
        """ Gets name of library """
        return self.get_selected_option_text(self.LIBRARY_LABEL)

    @library_name.setter
    def library_name(self, library_name):
        """
        Select a library from the library select box
        """
        self.set_select_value(self.LIBRARY_LABEL, library_name)
        EmptyPromise(lambda: self.library_name == library_name, "library_name is updated in modal.").fulfill()

    @property
    def count(self):
        """
        Gets value of children count input
        """
        return int(self.get_setting_element(self.COUNT_LABEL).get_attribute('value'))

    @count.setter
    def count(self, count):
        """
        Sets value of children count input
        """
        count_text = self.get_setting_element(self.COUNT_LABEL)
        count_text.send_keys(Keys.CONTROL, "a")
        count_text.send_keys(Keys.BACK_SPACE)
        count_text.send_keys(count)
        EmptyPromise(lambda: self.count == count, "count is updated in modal.").fulfill()

    @property
    def scored(self):
        """
        Gets value of scored select
        """
        value = self.get_selected_option_text(self.SCORED_LABEL)
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
        self.set_select_value(self.SCORED_LABEL, str(scored))
        EmptyPromise(lambda: self.scored == scored, "scored is updated in modal.").fulfill()

    @property
    def capa_type(self):
        """
        Gets value of CAPA type select
        """
        return self.get_setting_element(self.PROBLEM_TYPE_LABEL).get_attribute('value')

    @capa_type.setter
    def capa_type(self, value):
        """
        Sets value of CAPA type select
        """
        self.set_select_value(self.PROBLEM_TYPE_LABEL, value)
        EmptyPromise(lambda: self.capa_type == value, "problem type is updated in modal.").fulfill()

    def set_select_value(self, label, value):
        """
        Sets the select with given label (display name) to the specified value
        """
        elem = self.get_setting_element(label)
        select = Select(elem)
        select.select_by_value(value)


@js_defined('window.LibraryContentAuthorView')
class StudioLibraryContainerXBlockWrapper(XBlockWrapper):
    """
    Wraps :class:`.container.XBlockWrapper` for use with LibraryContent blocks
    """
    url = None

    def is_browser_on_page(self):
        """
        Returns true iff the library content area has been loaded
        """
        return self.q(css='article.content-primary').visible

    def is_finished_loading(self):
        """
        Returns true iff the Loading indicator is not visible
        """
        return not self.q(css='div.ui-loading').visible

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

    @wait_for_js  # Wait for the fragment.initialize_js('LibraryContentAuthorView') call to finish
    def refresh_children(self):
        """
        Click "Update now..." button
        """
        btn_selector = self._bounded_selector(".library-update-btn")
        self.wait_for_element_presence(btn_selector, 'Update now button is present.')
        self.q(css=btn_selector).first.click()

        # This causes a reload (see cms/static/xmodule_js/public/js/library_content_edit.js)
        # Check that the ajax request that caused the reload is done.
        self.wait_for_ajax()
        # Then check that we are still on the right page.
        self.wait_for(lambda: self.is_browser_on_page(), 'StudioLibraryContainerXBlockWrapper has reloaded.')
        # Wait longer than the default 60 seconds, because this was intermittently failing on jenkins
        # with the screenshot showing that the Loading indicator was still visible. See TE-745.
        self.wait_for(lambda: self.is_finished_loading(), 'Loading indicator is not visible.', timeout=120)

        # And wait to make sure the ajax post has finished.
        self.wait_for_ajax()
        self.wait_for_element_absence(btn_selector, 'Wait for the XBlock to finish reloading')

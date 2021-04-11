"""
Page classes to test either the Course Team page or the Library Team page.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from common.test.acceptance.tests.helpers import disable_animations


def wait_for_ajax_or_reload(browser):
    """
    Wait for all ajax requests to finish, OR for the page to reload.
    Normal wait_for_ajax() chokes on occasion if the pages reloads,
    giving "WebDriverException: Message: u'jQuery is not defined'"
    """
    def _is_ajax_finished():
        """ Wait for jQuery to finish all AJAX calls, if it is present. """
        return browser.execute_script("return typeof(jQuery) == 'undefined' || jQuery.active == 0")

    EmptyPromise(_is_ajax_finished, "Finished waiting for ajax requests.").fulfill()


class UsersPageMixin(PageObject):
    """ Common functionality for course/library team pages """
    new_user_form_selector = '.form-create.create-user .user-email-input'

    def url(self):
        """
        URL to this page - override in subclass
        """
        raise NotImplementedError

    def wait_until_ready(self):
        """
        When the page first loads, there is a loading indicator and most
        functionality is not yet available. This waits for that loading to
        finish.

        This method is different from wait_until_no_loading_indicator because this expects
        the loading indicator to still exist on the page; it is just hidden.

        It also disables animations for improved test reliability.
        """

        self.wait_for_element_invisibility(
            '.ui-loading',
            'Wait for the page to complete its initial loading'
        )
        disable_animations(self)

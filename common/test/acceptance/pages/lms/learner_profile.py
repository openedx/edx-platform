"""
Bok-Choy PageObject class for learner profile page.
"""
from bok_choy.query import BrowserQuery

from common.test.acceptance.pages.lms import BASE_URL
from bok_choy.page_object import PageObject
from common.test.acceptance.pages.lms.fields import FieldsMixin
from bok_choy.promise import EmptyPromise
from common.test.acceptance.pages.lms.instructor_dashboard import InstructorDashboardPage
from common.test.acceptance.tests.helpers import select_option_by_value
from selenium.webdriver import ActionChains


PROFILE_VISIBILITY_SELECTOR = '#u-field-select-account_privacy option[value="{}"]'
PROFILE_VISIBILITY_INPUT = '#u-field-select-account_privacy'
FIELD_ICONS = {
    'country': 'fa-map-marker',
    'language_proficiencies': 'fa-comment',
}


class Badge(PageObject):
    """
    Represents a single badge displayed on the learner profile page.
    """
    url = None

    def __init__(self, element, browser):
        self.element = element
        super(Badge, self).__init__(browser)

    def is_browser_on_page(self):
        return BrowserQuery(self.element, css=".badge-details").visible

    def modal_displayed(self):
        """
        Verifies that the share modal is diplayed.
        """
        # The modal is on the page at large, and not a subelement of the badge div.
        return self.q(css=".badges-modal").visible

    def display_modal(self):
        """
        Click the share button to display the sharing modal for the badge.
        """
        BrowserQuery(self.element, css=".share-button").click()
        EmptyPromise(self.modal_displayed, "Share modal displayed").fulfill()
        EmptyPromise(self.modal_focused, "Focus handed to modal").fulfill()

    def modal_focused(self):
        """
        Return True if the badges model has focus, False otherwise.
        """
        return self.q(css=".badges-modal").is_focused()

    def bring_model_inside_window(self):
        """
        Execute javascript to bring the popup(.badges-model) inside the window.
        """
        script_to_execute = ("var popup = document.querySelectorAll('.badges-modal')[0];;"
                             "popup.style.left = '20%';")
        self.browser.execute_script(script_to_execute)

    def close_modal(self):
        """
        Close the badges modal and check that it is no longer displayed.
        """
        # In chrome, close button is not inside window
        # which causes click failures. To avoid this, just change
        # the position of the popup
        self.bring_model_inside_window()
        self.q(css=".badges-modal .close").click()
        EmptyPromise(lambda: not self.modal_displayed(), "Share modal dismissed").fulfill()


class LearnerProfilePage(FieldsMixin, PageObject):
    """
    PageObject methods for Learning Profile Page.
    """

    def __init__(self, browser, username):
        """
        Initialize the page.

        Arguments:
            browser (Browser): The browser instance.
            username (str): Profile username.
        """
        super(LearnerProfilePage, self).__init__(browser)
        self.username = username

    @property
    def url(self):
        """
        Construct a URL to the page.
        """
        return BASE_URL + "/u/" + self.username

    def is_browser_on_page(self):
        """
        Check if browser is showing correct page.
        """
        return all([
            self.q(css='body.view-profile .account-settings-container').present,
            not self.q(css='ui-loading-indicator').visible
        ])

    @property
    def privacy(self):
        """
        Get user profile privacy.

        Returns:
            'all_users' or 'private'
        """
        return 'all_users' if self.q(css=PROFILE_VISIBILITY_SELECTOR.format('all_users')).selected else 'private'

    def accomplishments_available(self):
        """
        Verify that the accomplishments tab is available.
        """
        return self.q(css="button[data-url='accomplishments']").visible

    def display_accomplishments(self):
        """
        Click the accomplishments tab and wait for the accomplishments to load.
        """
        EmptyPromise(self.accomplishments_available, "Accomplishments tab is displayed").fulfill()
        self.q(css="button[data-url='accomplishments']").click()
        self.wait_for_element_visibility(".badge-list", "Badge list displayed")

    @property
    def badges(self):
        """
        Get all currently listed badges.
        """
        return [Badge(element, self.browser) for element in self.q(css=".badge-display:not(.badge-placeholder)")]

    @privacy.setter
    def privacy(self, privacy):
        """
        Set user profile privacy.

        Arguments:
            privacy (str): 'all_users' or 'private'
        """
        self.wait_for_element_visibility('select#u-field-select-account_privacy', 'Privacy dropdown is visible')

        if privacy != self.privacy:
            query = self.q(css=PROFILE_VISIBILITY_INPUT)
            select_option_by_value(query, privacy, focus_out=True)
            EmptyPromise(lambda: privacy == self.privacy, 'Privacy is set to {}'.format(privacy)).fulfill()
            self.wait_for_ajax()

            if privacy == 'all_users':
                self.wait_for_public_fields()

    def field_is_visible(self, field_id):
        """
        Check if a field with id set to `field_id` is shown.

        Arguments:
            field_id (str): field id

        Returns:
            True/False
        """
        self.wait_for_ajax()
        return self.q(css='.u-field-{}'.format(field_id)).visible

    def field_is_editable(self, field_id):
        """
        Check if a field with id set to `field_id` is editable.

        Arguments:
            field_id (str): field id

        Returns:
            True/False
        """
        self.wait_for_field(field_id)
        self.make_field_editable(field_id)
        return self.mode_for_field(field_id) == 'edit'

    @property
    def visible_fields(self):
        """
        Return list of visible fields.
        """
        self.wait_for_field('username')

        fields = ['username', 'country', 'language_proficiencies', 'bio']
        return [field for field in fields if self.field_is_visible(field)]

    @property
    def editable_fields(self):
        """
        Return list of editable fields currently shown on page.
        """
        self.wait_for_ajax()
        self.wait_for_element_visibility('.u-field-username', 'username is not visible')

        fields = ['country', 'language_proficiencies', 'bio']
        return [field for field in fields if self.field_is_editable(field)]

    @property
    def privacy_field_visible(self):
        """
        Check if profile visibility selector is shown or not.

        Returns:
            True/False
        """
        self.wait_for_ajax()
        return self.q(css='#u-field-select-account_privacy').visible

    def field_icon_present(self, field_id):
        """
        Check if an icon is present for a field. Only dropdown fields have icons.

        Arguments:
            field_id (str): field id

        Returns:
            True/False
        """
        return self.icon_for_field(field_id, FIELD_ICONS[field_id])

    def wait_for_public_fields(self):
        """
        Wait for `country`, `language` and `bio` fields to be visible.
        """
        EmptyPromise(lambda: self.field_is_visible('country'), 'Country field is visible').fulfill()
        EmptyPromise(lambda: self.field_is_visible('language_proficiencies'), 'Language field is visible').fulfill()
        EmptyPromise(lambda: self.field_is_visible('bio'), 'About Me field is visible').fulfill()

    @property
    def profile_forced_private_message(self):
        """
        Returns age limit message.
        """
        self.wait_for_ajax()
        return self.q(css='#u-field-message-account_privacy').text[0]

    @property
    def age_limit_message_present(self):
        """
        Check if age limit message is present.
        """
        self.wait_for_ajax()
        return self.q(css='#u-field-message-account_privacy').visible

    @property
    def profile_has_default_image(self):
        """
        Return bool if image field has default photo or not.
        """
        self.wait_for_field('image')
        default_links = self.q(css='.image-frame').attrs('src')
        return 'profiles/default' in default_links[0] if default_links else False

    def mouse_hover(self, element):
        """
        Mouse over on given element.
        """
        mouse_hover_action = ActionChains(self.browser).move_to_element(element)
        mouse_hover_action.perform()

    def profile_has_image_with_public_access(self):
        """
        Check if image is present with remove/upload access.
        """
        self.wait_for_field('image')

        self.mouse_hover(self.browser.find_element_by_css_selector('.image-wrapper'))
        self.wait_for_element_visibility('.u-field-upload-button', "upload button is visible")
        return self.q(css='.u-field-upload-button').visible

    def profile_has_image_with_private_access(self):
        """
        Check if image is present with remove/upload access.
        """
        self.wait_for_field('image')
        return self.q(css='.u-field-upload-button').visible

    def upload_file(self, filename, wait_for_upload_button=True):
        """
        Helper method to upload an image file.
        """
        if wait_for_upload_button:
            self.wait_for_element_visibility('.u-field-upload-button', "upload button is visible")
        file_path = InstructorDashboardPage.get_asset_path(filename)

        # make the elements visible.
        self.browser.execute_script('$(".u-field-upload-button").css("opacity",1);')
        self.browser.execute_script('$(".upload-button-input").css("opacity",1);')

        self.wait_for_element_visibility('.upload-button-input', "upload button is visible")

        self.browser.execute_script('$(".upload-submit").show();')

        self.q(css='.upload-submit').first.click()
        self.q(css='.upload-button-input').results[0].send_keys(file_path)
        self.wait_for_ajax()

    @property
    def image_upload_success(self):
        """
        Returns the bool, if image is updated or not.
        """
        self.wait_for_field('image')
        self.wait_for_ajax()

        self.wait_for_element_visibility('.image-frame', "image box is visible")
        image_link = self.q(css='.image-frame').attrs('src')
        return 'default-profile' not in image_link[0]

    @property
    def profile_image_message(self):
        """
        Returns the text message for profile image.
        """
        self.wait_for_field('image')
        self.wait_for_ajax()
        return self.q(css='.message-banner p').text[0]

    def remove_profile_image(self):
        """
        Removes the profile image.
        """
        self.wait_for_field('image')
        self.wait_for_ajax()

        self.wait_for_element_visibility('.image-wrapper', "remove button is visible")
        self.q(css='.u-field-remove-button').first.click()

        self.wait_for_ajax()
        self.mouse_hover(self.browser.find_element_by_css_selector('.image-wrapper'))
        self.wait_for_element_visibility('.u-field-upload-button', "upload button is visible")
        return True

    @property
    def remove_link_present(self):
        self.wait_for_field('image')
        self.mouse_hover(self.browser.find_element_by_css_selector('.image-wrapper'))
        return self.q(css='.u-field-remove-button').visible

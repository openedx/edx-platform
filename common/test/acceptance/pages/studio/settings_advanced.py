"""
Course Advanced Settings page
"""

from bok_choy.promise import EmptyPromise
from .course_page import CoursePage
from .utils import press_the_notification_button, type_in_codemirror, get_codemirror_value


KEY_CSS = '.key h3.title'
UNDO_BUTTON_SELECTOR = ".action-item .action-undo"
MANUAL_BUTTON_SELECTOR = ".action-item .action-cancel"
MODAL_SELECTOR = ".validation-error-modal-content"
ERROR_ITEM_NAME_SELECTOR = ".error-item-title strong"
ERROR_ITEM_CONTENT_SELECTOR = ".error-item-message"
SETTINGS_NAME_SELECTOR = ".is-not-editable"


class AdvancedSettingsPage(CoursePage):
    """
    Course Advanced Settings page.
    """

    url_path = "settings/advanced"

    def is_browser_on_page(self):
        def _is_finished_loading():
            return len(self.q(css='.course-advanced-policy-list-item')) > 0

        EmptyPromise(_is_finished_loading, 'Finished rendering the advanced policy items.').fulfill()
        return self.q(css='body.advanced').present

    def wait_for_modal_load(self):
        """
        Wait for validation response from the server, and make sure that
        the validation error modal pops up.

        This method should only be called when it is guaranteed that there're
        validation errors in the settings changes.
        """
        self.wait_for_ajax()
        self.wait_for_element_presence(MODAL_SELECTOR, 'Validation Modal is present')

    def refresh_and_wait_for_load(self):
        """
        Refresh the page and wait for all resources to load.
        """
        self.browser.refresh()
        self.wait_for_page()

    def coordinates_for_scrolling(self, coordinates_for):
        """
        Get the x and y coordinates of elements
        """
        cordinates_dict = self.browser.find_element_by_css_selector(coordinates_for)
        location = cordinates_dict.location
        for key, val in location.iteritems():
            if key == 'x':
                x_axis = val
            elif key == 'y':
                y_axis = val
        return x_axis, y_axis

    def undo_changes_via_modal(self):
        """
        Trigger clicking event of the undo changes button in the modal.
        Wait for the undoing process to load via ajax call.
        Before that Scroll so the button is clickable on all browsers
        """
        self.browser.execute_script("window.scrollTo" + str(self.coordinates_for_scrolling(UNDO_BUTTON_SELECTOR)))
        self.q(css=UNDO_BUTTON_SELECTOR).click()
        self.wait_for_ajax()

    def trigger_manual_changes(self):
        """
        Trigger click event of the manual changes button in the modal.
        No need to wait for any ajax.
        Before that Scroll so the button is clickable on all browsers
        """
        self.browser.execute_script("window.scrollTo" + str(self.coordinates_for_scrolling(MANUAL_BUTTON_SELECTOR)))
        self.q(css=MANUAL_BUTTON_SELECTOR).click()

    def is_validation_modal_present(self):
        """
        Checks if the validation modal is present.
        """
        return self.q(css=MODAL_SELECTOR).present

    def get_error_item_names(self):
        """
        Returns a list of display names of all invalid settings.
        """
        return self.q(css=ERROR_ITEM_NAME_SELECTOR).text

    def get_error_item_messages(self):
        """
        Returns a list of error messages of all invalid settings.
        """
        return self.q(css=ERROR_ITEM_CONTENT_SELECTOR).text

    def _get_index_of(self, expected_key):
        for i, element in enumerate(self.q(css=KEY_CSS)):
            # Sometimes get stale reference if I hold on to the array of elements
            key = self.q(css=KEY_CSS).nth(i).text[0]
            if key == expected_key:
                return i

        return -1

    def save(self):
        press_the_notification_button(self, "Save")

    def cancel(self):
        press_the_notification_button(self, "Cancel")

    def set(self, key, new_value):
        index = self._get_index_of(key)
        type_in_codemirror(self, index, new_value)
        self.save()

    def get(self, key):
        index = self._get_index_of(key)
        return get_codemirror_value(self, index)

    def set_values(self, key_value_map):
        """
        Make multiple settings changes and save them.
        """
        for key, value in key_value_map.iteritems():
            index = self._get_index_of(key)
            type_in_codemirror(self, index, value)

        self.save()

    def get_values(self, key_list):
        """
        Get a key-value dictionary of all keys in the given list.
        """
        result_map = {}

        for key in key_list:
            index = self._get_index_of(key)
            val = get_codemirror_value(self, index)
            result_map[key] = val

        return result_map

    @property
    def displayed_settings_names(self):
        """
        Returns all settings displayed on the advanced settings page/screen/modal/whatever
        We call it 'name', but it's really whatever is embedded in the 'id' element for each field
        """
        query = self.q(css=SETTINGS_NAME_SELECTOR)
        return query.attrs('id')

    @property
    def expected_settings_names(self):
        """
        Returns a list of settings expected to be displayed on the Advanced Settings screen
        Should match the list of settings found in cms/djangoapps/models/settings/course_metadata.py
        If a new setting is added to the metadata list, this test will fail and you must update it.
        Basically this guards against accidental exposure of a field on the Advanced Settings screen
        """
        return [
            'advanced_modules',
            'allow_anonymous',
            'allow_anonymous_to_peers',
            'allow_public_wiki_access',
            'cert_html_view_overrides',
            'cert_name_long',
            'cert_name_short',
            'certificates_display_behavior',
            'cohort_config',
            'course_image',
            'banner_image',
            'video_thumbnail_image',
            'cosmetic_display_price',
            'advertised_start',
            'announcement',
            'display_name',
            'info_sidebar_name',
            'is_new',
            'issue_badges',
            'max_student_enrollments_allowed',
            'no_grade',
            'display_coursenumber',
            'display_organization',
            'catalog_visibility',
            'days_early_for_beta',
            'disable_progress_graph',
            'discussion_blackouts',
            'discussion_sort_alpha',
            'discussion_topics',
            'due',
            'due_date_display_format',
            'edxnotes',
            'use_latex_compiler',
            'video_speed_optimizations',
            'enrollment_domain',
            'html_textbooks',
            'invitation_only',
            'lti_passports',
            'matlab_api_key',
            'max_attempts',
            'mobile_available',
            'rerandomize',
            'remote_gradebook',
            'annotation_token_secret',
            'showanswer',
            'show_calculator',
            'show_reset_button',
            'static_asset_path',
            'teams_configuration',
            'text_customization',
            'annotation_storage_url',
            'social_sharing_url',
            'video_bumper',
            'cert_html_view_enabled',
            'enable_proctored_exams',
            'enable_timed_exams',
            'enable_subsection_gating',
            'learning_info',
            'instructor_info',
            'create_zendesk_tickets',
            'ccx_connector',
            'enable_ccx'
        ]

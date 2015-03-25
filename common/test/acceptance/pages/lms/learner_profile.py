"""
Bok-Choy PageObject class for learner profile page.
"""
from . import BASE_URL
from bok_choy.page_object import PageObject
from .fields import FieldsMixin


PROFILE_VISIBILITY_SELECTOR = '#u-field-select-account_privacy option[value="{}"]'
FIELD_ICONS = {
    'country': 'fa-map-marker',
    'language': 'fa-comment',
}


class LearnerProfilePage(FieldsMixin, PageObject):
    """
    PageObject methods for Learning Profile Page.
    """

    def __init__(self, browser, username):
        """
        """
        super(LearnerProfilePage, self).__init__(browser)
        self.username = username

    @property
    def url(self):
        return BASE_URL + "/u/" + self.username

    def is_browser_on_page(self):
        return 'Learner Profile' in self.browser.title

    @property
    def privacy(self):
        """
        Get user profile privacy.

        Returns:
            'all_users' or 'private'
        """
        return 'all_users' if self.q(css=PROFILE_VISIBILITY_SELECTOR.format('all_users')).selected else 'private'

    @privacy.setter
    def privacy(self, privacy):
        """
        Set user profile privacy.
        """
        self.q(css=PROFILE_VISIBILITY_SELECTOR.format(privacy)).first.click()
        self.wait_for_ajax()

    def field_is_visible(self, field_id):
        """
        Check if a field with id set to `field_id` is shown.

        Arguement:
            field_id (str): field id

        Returns:
            True/False
        """
        return self.q(css='.u-field-{}'.format(field_id)).visible

    @property
    def visible_fields(self):
        """
        Return list of visible fields.
        """
        fields = ['username', 'country', 'language', 'bio']
        return [field for field in fields if self.field_is_visible(field)]

    @property
    def privacy_field_visible(self):
        """
        Check if profile visibility selector is shown or not.

        Returns:
            True/False
        """
        return self.q(css='#u-field-select-account_privacy').visible

    def country(self, value=None):
        """
        Get or set language.
        """
        return self.value_for_dropdown_field('country', value)

    def language(self, value=None):
        """
        Get or set country.
        """
        return self.value_for_dropdown_field('language', value)

    def aboutme(self, value=None):
        """
        Get or set aboutme.
        """
        return self.value_for_textarea_field('bio', value)

    def field_icon_present(self, field_id):
        """
        Check if an icon is present for a field. Please note only dropdown fields have icons.
        """
        return self.icon_for_field(field_id, FIELD_ICONS[field_id])

    def fields_editability(self, own_profile):
        """
        Check fields are editable/non-editable whether a user is viewing her own profile or another profile.

        Arguments:
            own_profile (bool):

        Returns:
            True/False
        """
        return True
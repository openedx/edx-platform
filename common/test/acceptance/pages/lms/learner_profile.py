"""
Bok-Choy PageObject class for learner profile page.
"""
from . import BASE_URL
from bok_choy.page_object import PageObject
from .fields import FieldsMixin
from bok_choy.promise import EmptyPromise


PROFILE_VISIBILITY_SELECTOR = '#u-field-select-account_privacy option[value="{}"]'
FIELD_ICONS = {
    'country': 'fa-map-marker',
    'language_proficiencies': 'fa-comment',
}


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

        Arguments:
            privacy (str): 'all_users' or 'private'
        """
        self.wait_for_element_visibility('select#u-field-select-account_privacy', 'Privacy dropdown is visiblie')

        if privacy != self.privacy:
            self.q(css=PROFILE_VISIBILITY_SELECTOR.format(privacy)).first.click()
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

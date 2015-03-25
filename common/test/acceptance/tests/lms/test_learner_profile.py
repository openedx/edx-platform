# -*- coding: utf-8 -*-
"""
End-to-end tests for Student's Profile Page.
"""

from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.learner_profile import LearnerProfilePage
from ...pages.lms.dashboard import DashboardPage

from bok_choy.web_app_test import WebAppTest


class LearnerProfilePageTest(WebAppTest):
    """
    Tests that verify Student's Profile Page.
    """

    USER_ONE_NAME = 'user1'
    USER_ONE_EMAIL = 'user1@edx.org'
    USER_TWO_NAME = 'user2'
    USER_TWO_EMAIL = 'user2@edx.org'

    MY_USER = 1
    OTHER_USER = 2

    PRIVACY_PUBLIC = 'all_users'
    PRIVACY_PRIVATE = 'private'

    PUBLIC_PROFILE_FIELDS = ['username', 'country', 'language', 'bio']
    PRIVATE_PROFILE_FIELDS = ['username']

    def setUp(self):
        """
        Initialize pages.
        """
        super(LearnerProfilePageTest, self).setUp()
        self.dashboard_page = DashboardPage(self.browser)

        self.my_auto_auth_page = AutoAuthPage(self.browser, username=self.USER_ONE_NAME, email=self.USER_ONE_EMAIL).visit()
        self.my_profile_page = LearnerProfilePage(self.browser, self.USER_ONE_NAME)

        self.other_auto_auth_page = AutoAuthPage(self.browser, username=self.USER_TWO_NAME, email=self.USER_TWO_EMAIL).visit()
        self.other_profile_page = LearnerProfilePage(self.browser, self.USER_TWO_NAME)

    def authenticate_as_user(self, user):
        if user == self.MY_USER:
            self.my_auto_auth_page.visit()
        elif user == self.OTHER_USER:
            self.other_auto_auth_page.visit()

    def visit_my_profile_page(self, user, privacy=None):
        self.authenticate_as_user(user)
        self.my_profile_page.visit()
        self.my_profile_page.wait_for_page()

        if user is self.MY_USER and privacy is not None:
            self.my_profile_page.privacy = privacy

    def visit_other_profile_page(self, user, privacy=None):
        self.authenticate_as_user(user)
        self.other_profile_page.visit()
        self.other_profile_page.wait_for_page()

        if user is self.OTHER_USER and privacy is not None:
            self.other_profile_page.privacy = privacy

            if privacy == self.PRIVACY_PUBLIC:
                self.other_profile_page.language('English')
                self.other_profile_page.country('United Kingdom')
                self.other_profile_page.aboutme('Nothing Special')

    def test_dashboard_learner_profile_link(self):
        """
        Scenario: Verify that my profile link is present on dashboard page and we can navigate to correct page.

        Given that I am a registered user.
        When I go to Dashboard page.
        And I click on username dropdown.
        Then I see My Profile link in the dropdown menu.
        When I click on My Profile link.
        Then I will be navigated to My Profile page.
        """
        self.dashboard_page.visit()
        self.dashboard_page.click_username_dropdown()
        self.assertTrue('My Profile' in self.dashboard_page.username_dropdown_link_text)
        self.dashboard_page.click_my_profile_link()
        self.my_profile_page.wait_for_page()

    def _verify_profile_fields(self, visibility, own_profile=True):
        """
        Verify that desired fields are shown when profile visibility set to `visibility`

        Arguments:
            visibility (str): 'all_users' or 'private'
        """
        self.learner_profile_page.visibility = visibility

        self.browser.refresh()
        self.learner_profile_page.wait_for_page()

        # Verify that fields are shown/hidden according to the profile visibility
        self.assertTrue(self.learner_profile_page.fields_visibility(visibility))

        # Verify that profile visibility selector is shown/hidden according to own_profile
        self.assertEqual(self.learner_profile_page.visibility_selector_state, own_profile)

        # Verify that fields are editable/non-editable whether a user is viewing her own profile or another profile
        self.assertTrue(self.learner_profile_page.fields_editability(own_profile))

    def test_fields_on_my_private_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at her own private profile.

        Given that I am a registered user.
        And I visit My Profile page.
        And I set the profile visibility to private.
        And I reload the page.
        Then I should see the profile visibility selector dropdown.
        Then I see some of the profile fields are shown.
        """
        self.visit_my_profile_page(self.MY_USER, privacy=self.PRIVACY_PRIVATE)

        self.assertTrue(self.my_profile_page.privacy_field_visible)
        self.assertEqual(self.my_profile_page.visible_fields, self.PRIVATE_PROFILE_FIELDS)

    def test_fields_on_my_public_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at her own public profile.

        Given that I am a registered user.
        And I visit My Profile page.
        And I set the profile visibility to public.
        And I reload the page.
        Then I should see the profile visibility selector dropdown.
        Then I see all the profile fields are shown.
        And `location`, `language` and `aboutme` fields are editable.
        """
        self.visit_my_profile_page(self.MY_USER, privacy=self.PRIVACY_PUBLIC)

        self.assertTrue(self.my_profile_page.privacy_field_visible)
        self.assertEqual(self.my_profile_page.visible_fields, self.PUBLIC_PROFILE_FIELDS)

    def test_fields_on_others_private_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at her own private profile.

        Given that I am a registered user.
        And I visit My Profile page.
        And I set the profile visibility to private.
        And I reload the page.
        Then I shouldn't see the profile visibility selector dropdown.
        Then I see some of the profile fields are shown.
        """
        self.visit_other_profile_page(self.OTHER_USER, privacy=self.PRIVACY_PRIVATE)
        self.visit_other_profile_page(self.MY_USER)

        self.assertFalse(self.other_profile_page.privacy_field_visible)
        self.assertEqual(self.other_profile_page.visible_fields, self.PRIVATE_PROFILE_FIELDS)

    def test_fields_on_others_public_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at her own public profile.

        Given that I am a registered user.
        And I visit My Profile page.
        And I set the profile visibility to public.
        And I reload the page.
        Then I shouldn't see the profile visibility selector dropdown.
        Then I see all the profile fields are shown.
        And `location`, `language` and `aboutme` fields are not editable.
        """
        self.visit_other_profile_page(self.OTHER_USER, privacy=self.PRIVACY_PUBLIC)
        self.visit_other_profile_page(self.MY_USER)

        self.assertFalse(self.other_profile_page.privacy_field_visible)

        # We are excluding language field from verification because when a usr view another users profile,
        # server send `languages` field in model instead of `language`, due to which langauge field will not be shown
        # Untill this is fixed on server side, we will exclude the language fields.
        fields_to_check = self.PUBLIC_PROFILE_FIELDS[0:2] + self.PUBLIC_PROFILE_FIELDS[3:]
        self.assertEqual(self.other_profile_page.visible_fields, fields_to_check)

    def _test_dropdown_field(self, field_id, new_value, displayed_value, mode):
        self.visit_my_profile_page(self.MY_USER, privacy=self.PRIVACY_PUBLIC)

        self.my_profile_page.value_for_dropdown_field(field_id, new_value)
        self.assertEqual(self.my_profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(self.my_profile_page.mode_for_field(field_id), mode)

        self.browser.refresh()
        self.my_profile_page.wait_for_page()

        self.assertEqual(self.my_profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(self.my_profile_page.mode_for_field(field_id), mode)

    def _test_textarea_field(self, field_id, new_value, displayed_value, mode):
        """
        Test behaviour of a textarea field.
        """
        self.visit_my_profile_page(self.MY_USER, privacy=self.PRIVACY_PUBLIC)

        self.my_profile_page.value_for_textarea_field(field_id, new_value)
        self.assertEqual(self.my_profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(self.my_profile_page.mode_for_field(field_id), mode)

        self.browser.refresh()
        self.my_profile_page.wait_for_page()

        self.assertEqual(self.my_profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(self.my_profile_page.mode_for_field(field_id), mode)

    def test_country_field(self):
        """
        Test behaviour of `Country` field.
        """
        self._test_dropdown_field('country', 'Pakistan', 'Pakistan', 'display')

        self.my_profile_page.make_field_editable('country')
        self.assertTrue(self.my_profile_page.mode_for_field('country'), 'edit')

    def test_language_field(self):
        """
        Test behaviour of `Language` field.
        """
        self._test_dropdown_field('language', 'Urdu', 'Urdu', 'display')
        self._test_dropdown_field('language', '', 'Add language', 'placeholder')

        self.my_profile_page.make_field_editable('language')
        self.assertTrue(self.my_profile_page.mode_for_field('language'), 'edit')

    def test_aboutme_field(self):
        """
        Test behaviour of `About Me` field.
        """
        placeholder_value = (
            "Tell other edX learners a little about yourself, where you're from, "
            "what your interests are, why you joined edX, what you hope to learn..."
        )

        self._test_textarea_field('bio', 'Eat Sleep Code', 'Eat Sleep Code', 'display')
        self._test_textarea_field('bio', '', placeholder_value, 'placeholder')

        self.my_profile_page.make_field_editable('bio')
        self.assertTrue(self.my_profile_page.mode_for_field('bio'), 'edit')

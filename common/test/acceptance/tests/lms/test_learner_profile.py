# -*- coding: utf-8 -*-
"""
End-to-end tests for Student's Profile Page.
"""
from contextlib import contextmanager

from datetime import datetime
from bok_choy.web_app_test import WebAppTest
from nose.plugins.attrib import attr

from ...pages.common.logout import LogoutPage
from ...pages.lms.account_settings import AccountSettingsPage
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.learner_profile import LearnerProfilePage
from ...pages.lms.dashboard import DashboardPage

from ..helpers import EventsTestMixin


class LearnerProfileTestMixin(EventsTestMixin):
    """
    Mixin with helper methods for testing learner profile pages.
    """

    PRIVACY_PUBLIC = u'all_users'
    PRIVACY_PRIVATE = u'private'

    PUBLIC_PROFILE_FIELDS = ['username', 'country', 'language_proficiencies', 'bio']
    PRIVATE_PROFILE_FIELDS = ['username']

    PUBLIC_PROFILE_EDITABLE_FIELDS = ['country', 'language_proficiencies', 'bio']

    USER_SETTINGS_CHANGED_EVENT_NAME = u"edx.user.settings.changed"

    def log_in_as_unique_user(self):
        """
        Create a unique user and return the account's username and id.
        """
        username = "test_{uuid}".format(uuid=self.unique_id[0:6])
        auto_auth_page = AutoAuthPage(self.browser, username=username).visit()
        user_id = auto_auth_page.get_user_id()
        return username, user_id

    def set_public_profile_fields_data(self, profile_page):
        """
        Fill in the public profile fields of a user.
        """
        profile_page.value_for_dropdown_field('language_proficiencies', 'English')
        profile_page.value_for_dropdown_field('country', 'United Arab Emirates')
        profile_page.set_value_for_textarea_field('bio', 'Nothing Special')

    def visit_profile_page(self, username, privacy=None):
        """
        Visit a user's profile page and if a privacy is specified and
        is different from the displayed value, then set the privacy to that value.
        """
        profile_page = LearnerProfilePage(self.browser, username)

        # Change the privacy if requested by loading the page and
        # changing the drop down
        if privacy is not None:
            profile_page.visit()

            # Change the privacy setting if it is not the desired one already
            profile_page.privacy = privacy

            # Verify the current setting is as expected
            if privacy == self.PRIVACY_PUBLIC:
                self.assertEqual(profile_page.privacy, 'all_users')
            else:
                self.assertEqual(profile_page.privacy, 'private')

            if privacy == self.PRIVACY_PUBLIC:
                self.set_public_profile_fields_data(profile_page)

        # Reset event tracking so that the tests only see events from
        # loading the profile page.
        self.start_time = datetime.now()  # pylint: disable=attribute-defined-outside-init

        # Load the page
        profile_page.visit()

        return profile_page

    def set_birth_year(self, birth_year):
        """
        Set birth year for the current user to the specified value.
        """
        account_settings_page = AccountSettingsPage(self.browser)
        account_settings_page.visit()
        account_settings_page.wait_for_page()
        self.assertEqual(
            account_settings_page.value_for_dropdown_field('year_of_birth', str(birth_year)),
            str(birth_year)
        )

    def verify_profile_page_is_public(self, profile_page, is_editable=True):
        """
        Verify that the profile page is currently public.
        """
        self.assertEqual(profile_page.visible_fields, self.PUBLIC_PROFILE_FIELDS)
        if is_editable:
            self.assertTrue(profile_page.privacy_field_visible)
            self.assertEqual(profile_page.editable_fields, self.PUBLIC_PROFILE_EDITABLE_FIELDS)
        else:
            self.assertEqual(profile_page.editable_fields, [])

    def verify_profile_page_is_private(self, profile_page, is_editable=True):
        """
        Verify that the profile page is currently private.
        """
        if is_editable:
            self.assertTrue(profile_page.privacy_field_visible)
        self.assertEqual(profile_page.visible_fields, self.PRIVATE_PROFILE_FIELDS)

    def verify_profile_page_view_event(self, requesting_username, profile_user_id, visibility=None):
        """
        Verifies that the correct view event was captured for the profile page.
        """

        actual_events = self.wait_for_events(
            start_time=self.start_time,
            event_filter={'event_type': 'edx.user.settings.viewed', 'username': requesting_username},
            number_of_matches=1)
        self.assert_events_match(
            [
                {
                    'username': requesting_username,
                    'event': {
                        'user_id': int(profile_user_id),
                        'page': 'profile',
                        'visibility': unicode(visibility)
                    }
                }
            ],
            actual_events
        )

    @contextmanager
    def verify_pref_change_event_during(self, username, user_id, setting, **kwargs):
        """Assert that a single setting changed event is emitted for the user_api_userpreference table."""
        expected_event = {
            'username': username,
            'event': {
                'setting': setting,
                'user_id': int(user_id),
                'table': 'user_api_userpreference',
                'truncated': []
            }
        }
        expected_event['event'].update(kwargs)

        event_filter = {
            'event_type': self.USER_SETTINGS_CHANGED_EVENT_NAME,
            'username': username,
        }
        with self.assert_events_match_during(event_filter=event_filter, expected_events=[expected_event]):
            yield

    def initialize_different_user(self, privacy=None, birth_year=None):
        """
        Initialize the profile page for a different test user
        """
        username, user_id = self.log_in_as_unique_user()

        # Set the privacy for the new user
        if privacy is None:
            privacy = self.PRIVACY_PUBLIC
        self.visit_profile_page(username, privacy=privacy)

        # Set the user's year of birth
        if birth_year:
            self.set_birth_year(birth_year)

        # Log the user out
        LogoutPage(self.browser).visit()

        return username, user_id


@attr('shard_4')
class OwnLearnerProfilePageTest(LearnerProfileTestMixin, WebAppTest):
    """
    Tests that verify a student's own profile page.
    """

    def verify_profile_forced_private_message(self, username, birth_year, message=None):
        """
        Verify age limit messages for a user.
        """
        if birth_year is None:
            birth_year = ""
        self.set_birth_year(birth_year=birth_year)
        profile_page = self.visit_profile_page(username)
        self.assertTrue(profile_page.privacy_field_visible)
        if message:
            self.assertTrue(profile_page.age_limit_message_present)
        else:
            self.assertFalse(profile_page.age_limit_message_present)
        self.assertIn(message, profile_page.profile_forced_private_message)

    def test_profile_defaults_to_public(self):
        """
        Scenario: Verify that a new user's profile defaults to public.

        Given that I am a new user.
        When I go to my profile page.
        Then I see that the profile visibility is set to public.
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username)
        self.verify_profile_page_is_public(profile_page)

    def assert_default_image_has_public_access(self, profile_page):
        """
        Assert that profile image has public access.
        """
        self.assertTrue(profile_page.profile_has_default_image)
        self.assertTrue(profile_page.profile_has_image_with_public_access())

    def test_make_profile_public(self):
        """
        Scenario: Verify that the user can change their privacy.

        Given that I am a registered user
        And I visit my private profile page
        And I set the profile visibility to public
        Then a user preference changed event should be recorded
        When I reload the page
        Then the profile visibility should be shown as public
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PRIVATE)
        with self.verify_pref_change_event_during(
            username, user_id, 'account_privacy', old=self.PRIVACY_PRIVATE, new=self.PRIVACY_PUBLIC
        ):
            profile_page.privacy = self.PRIVACY_PUBLIC

        # Reload the page and verify that the profile is now public
        self.browser.refresh()
        profile_page.wait_for_page()
        self.verify_profile_page_is_public(profile_page)

    def test_make_profile_private(self):
        """
        Scenario: Verify that the user can change their privacy.

        Given that I am a registered user
        And I visit my public profile page
        And I set the profile visibility to private
        Then a user preference changed event should be recorded
        When I reload the page
        Then the profile visibility should be shown as private
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)
        with self.verify_pref_change_event_during(
            username, user_id, 'account_privacy', old=None, new=self.PRIVACY_PRIVATE
        ):
            profile_page.privacy = self.PRIVACY_PRIVATE

        # Reload the page and verify that the profile is now private
        self.browser.refresh()
        profile_page.wait_for_page()
        self.verify_profile_page_is_private(profile_page)

    def test_dashboard_learner_profile_link(self):
        """
        Scenario: Verify that my profile link is present on dashboard page and we can navigate to correct page.

        Given that I am a registered user.
        When I go to Dashboard page.
        And I click on username dropdown.
        Then I see Profile link in the dropdown menu.
        When I click on Profile link.
        Then I will be navigated to Profile page.
        """
        username, user_id = self.log_in_as_unique_user()
        dashboard_page = DashboardPage(self.browser)
        dashboard_page.visit()
        dashboard_page.click_username_dropdown()
        self.assertIn('Profile', dashboard_page.username_dropdown_link_text)
        dashboard_page.click_my_profile_link()
        my_profile_page = LearnerProfilePage(self.browser, username)
        my_profile_page.wait_for_page()

    def test_fields_on_my_private_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at her own private profile.

        Given that I am a registered user.
        And I visit my Profile page.
        And I set the profile visibility to private.
        And I reload the page.
        Then I should see the profile visibility selector dropdown.
        Then I see some of the profile fields are shown.
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PRIVATE)
        self.verify_profile_page_is_private(profile_page)
        self.verify_profile_page_view_event(username, user_id, visibility=self.PRIVACY_PRIVATE)

    def test_fields_on_my_public_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at her own public profile.

        Given that I am a registered user.
        And I visit my Profile page.
        And I set the profile visibility to public.
        And I reload the page.
        Then I should see the profile visibility selector dropdown.
        Then I see all the profile fields are shown.
        And `location`, `language` and `about me` fields are editable.
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)
        self.verify_profile_page_is_public(profile_page)
        self.verify_profile_page_view_event(username, user_id, visibility=self.PRIVACY_PUBLIC)

    def _test_dropdown_field(self, profile_page, field_id, new_value, displayed_value, mode):
        """
        Test behaviour of a dropdown field.
        """
        profile_page.value_for_dropdown_field(field_id, new_value)
        self.assertEqual(profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(profile_page.mode_for_field(field_id), mode)

        self.browser.refresh()
        profile_page.wait_for_page()

        self.assertEqual(profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(profile_page.mode_for_field(field_id), mode)

    def _test_textarea_field(self, profile_page, field_id, new_value, displayed_value, mode):
        """
        Test behaviour of a textarea field.
        """
        profile_page.set_value_for_textarea_field(field_id, new_value)
        self.assertEqual(profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(profile_page.mode_for_field(field_id), mode)

        self.browser.refresh()
        profile_page.wait_for_page()

        self.assertEqual(profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(profile_page.mode_for_field(field_id), mode)

    def test_country_field(self):
        """
        Test behaviour of `Country` field.

        Given that I am a registered user.
        And I visit my Profile page.
        And I set the profile visibility to public and set default values for public fields.
        Then I set country value to `Pakistan`.
        Then displayed country should be `Pakistan` and country field mode should be `display`
        And I reload the page.
        Then displayed country should be `Pakistan` and country field mode should be `display`
        And I make `country` field editable
        Then `country` field mode should be `edit`
        And `country` field icon should be visible.
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)
        self._test_dropdown_field(profile_page, 'country', 'Pakistan', 'Pakistan', 'display')

        profile_page.make_field_editable('country')
        self.assertEqual(profile_page.mode_for_field('country'), 'edit')

        self.assertTrue(profile_page.field_icon_present('country'))

    def test_language_field(self):
        """
        Test behaviour of `Language` field.

        Given that I am a registered user.
        And I visit my Profile page.
        And I set the profile visibility to public and set default values for public fields.
        Then I set language value to `Urdu`.
        Then displayed language should be `Urdu` and language field mode should be `display`
        And I reload the page.
        Then displayed language should be `Urdu` and language field mode should be `display`
        Then I set empty value for language.
        Then displayed language should be `Add language` and language field mode should be `placeholder`
        And I reload the page.
        Then displayed language should be `Add language` and language field mode should be `placeholder`
        And I make `language` field editable
        Then `language` field mode should be `edit`
        And `language` field icon should be visible.
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)
        self._test_dropdown_field(profile_page, 'language_proficiencies', 'Urdu', 'Urdu', 'display')
        self._test_dropdown_field(profile_page, 'language_proficiencies', '', 'Add language', 'placeholder')

        profile_page.make_field_editable('language_proficiencies')
        self.assertTrue(profile_page.mode_for_field('language_proficiencies'), 'edit')

        self.assertTrue(profile_page.field_icon_present('language_proficiencies'))

    def test_about_me_field(self):
        """
        Test behaviour of `About Me` field.

        Given that I am a registered user.
        And I visit my Profile page.
        And I set the profile visibility to public and set default values for public fields.
        Then I set about me value to `ThisIsIt`.
        Then displayed about me should be `ThisIsIt` and about me field mode should be `display`
        And I reload the page.
        Then displayed about me should be `ThisIsIt` and about me field mode should be `display`
        Then I set empty value for about me.
        Then displayed about me should be `Tell other learners a little about yourself: where you live,
        what your interests are, why you're taking courses, or what you hope to learn.` and about me
        field mode should be `placeholder`
        And I reload the page.
        Then displayed about me should be `Tell other learners a little about yourself: where you live,
        what your interests are, why you're taking courses, or what you hope to learn.` and about me
        field mode should be `placeholder`
        And I make `about me` field editable
        Then `about me` field mode should be `edit`
        """
        placeholder_value = (
            "Tell other learners a little about yourself: where you live, what your interests are, "
            "why you're taking courses, or what you hope to learn."
        )

        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)
        self._test_textarea_field(profile_page, 'bio', 'ThisIsIt', 'ThisIsIt', 'display')
        self._test_textarea_field(profile_page, 'bio', '', placeholder_value, 'placeholder')

        profile_page.make_field_editable('bio')
        self.assertTrue(profile_page.mode_for_field('bio'), 'edit')

    def test_birth_year_not_set(self):
        """
        Verify message if birth year is not set.

        Given that I am a registered user.
        And birth year is not set for the user.
        And I visit my profile page.
        Then I should see a message that the profile is private until the year of birth is set.
        """
        username, user_id = self.log_in_as_unique_user()
        message = "You must specify your birth year before you can share your full profile."
        self.verify_profile_forced_private_message(username, birth_year=None, message=message)
        self.verify_profile_page_view_event(username, user_id, visibility=self.PRIVACY_PRIVATE)

    def test_user_is_under_age(self):
        """
        Verify message if user is under age.

        Given that I am a registered user.
        And birth year is set so that age is less than 13.
        And I visit my profile page.
        Then I should see a message that the profile is private as I am under thirteen.
        """
        username, user_id = self.log_in_as_unique_user()
        under_age_birth_year = datetime.now().year - 10
        self.verify_profile_forced_private_message(
            username,
            birth_year=under_age_birth_year,
            message='You must be over 13 to share a full profile.'
        )
        self.verify_profile_page_view_event(username, user_id, visibility=self.PRIVACY_PRIVATE)

    def test_user_can_only_see_default_image_for_private_profile(self):
        """
        Scenario: Default profile image behaves correctly for under age user.

        Given that I am on my profile page with private access
        And I can see default image
        When I move my cursor to the image
        Then i cannot see the upload/remove image text
        And i cannot upload/remove the image.
        """
        year_of_birth = datetime.now().year - 5
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PRIVATE)

        self.verify_profile_forced_private_message(
            username,
            year_of_birth,
            message='You must be over 13 to share a full profile.'
        )
        self.assertTrue(profile_page.profile_has_default_image)
        self.assertFalse(profile_page.profile_has_image_with_private_access())

    def test_user_can_see_default_image_for_public_profile(self):
        """
        Scenario: Default profile image behaves correctly for public profile.

        Given that I am on my profile page with public access
        And I can see default image
        When I move my cursor to the image
        Then i can see the upload/remove image text
        And i am able to upload new image
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)

        self.assert_default_image_has_public_access(profile_page)

    def test_user_can_upload_the_profile_image_with_success(self):
        """
        Scenario: Upload profile image works correctly.

        Given that I am on my profile page with public access
        And I can see default image
        When I move my cursor to the image
        Then i can see the upload/remove image text
        When i upload new image via file uploader
        Then i can see the changed image
        And i can also see the latest image after reload.
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)

        self.assert_default_image_has_public_access(profile_page)

        with self.verify_pref_change_event_during(
            username, user_id, 'profile_image_uploaded_at', table='auth_userprofile'
        ):
            profile_page.upload_file(filename='image.jpg')
        self.assertTrue(profile_page.image_upload_success)
        profile_page.visit()
        self.assertTrue(profile_page.image_upload_success)

    def test_user_can_see_error_for_exceeding_max_file_size_limit(self):
        """
        Scenario: Upload profile image does not work for > 1MB image file.

        Given that I am on my profile page with public access
        And I can see default image
        When I move my cursor to the image
        Then i can see the upload/remove image text
        When i upload new > 1MB image via file uploader
        Then i can see the error message for file size limit
        And i can still see the default image after page reload.
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)

        self.assert_default_image_has_public_access(profile_page)

        profile_page.upload_file(filename='larger_image.jpg')
        self.assertEqual(profile_page.profile_image_message, "The file must be smaller than 1 MB in size.")
        profile_page.visit()
        self.assertTrue(profile_page.profile_has_default_image)

        self.assert_no_matching_events_were_emitted({
            'event_type': self.USER_SETTINGS_CHANGED_EVENT_NAME,
            'event': {
                'setting': 'profile_image_uploaded_at',
                'user_id': int(user_id),
            }
        })

    def test_user_can_see_error_for_file_size_below_the_min_limit(self):
        """
        Scenario: Upload profile image does not work for < 100 Bytes image file.

        Given that I am on my profile page with public access
        And I can see default image
        When I move my cursor to the image
        Then i can see the upload/remove image text
        When i upload new < 100 Bytes image via file uploader
        Then i can see the error message for minimum file size limit
        And i can still see the default image after page reload.
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)

        self.assert_default_image_has_public_access(profile_page)

        profile_page.upload_file(filename='list-icon-visited.png')
        self.assertEqual(profile_page.profile_image_message, "The file must be at least 100 bytes in size.")
        profile_page.visit()
        self.assertTrue(profile_page.profile_has_default_image)

        self.assert_no_matching_events_were_emitted({
            'event_type': self.USER_SETTINGS_CHANGED_EVENT_NAME,
            'event': {
                'setting': 'profile_image_uploaded_at',
                'user_id': int(user_id),
            }
        })

    def test_user_can_see_error_for_wrong_file_type(self):
        """
        Scenario: Upload profile image does not work for wrong file types.

        Given that I am on my profile page with public access
        And I can see default image
        When I move my cursor to the image
        Then i can see the upload/remove image text
        When i upload new csv file via file uploader
        Then i can see the error message for wrong/unsupported file type
        And i can still see the default image after page reload.
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)

        self.assert_default_image_has_public_access(profile_page)

        profile_page.upload_file(filename='generic_csv.csv')
        self.assertEqual(
            profile_page.profile_image_message,
            "The file must be one of the following types: .gif, .png, .jpeg, .jpg."
        )
        profile_page.visit()
        self.assertTrue(profile_page.profile_has_default_image)

        self.assert_no_matching_events_were_emitted({
            'event_type': self.USER_SETTINGS_CHANGED_EVENT_NAME,
            'event': {
                'setting': 'profile_image_uploaded_at',
                'user_id': int(user_id),
            }
        })

    def test_user_can_remove_profile_image(self):
        """
        Scenario: Remove profile image works correctly.

        Given that I am on my profile page with public access
        And I can see default image
        When I move my cursor to the image
        Then i can see the upload/remove image text
        When i click on the remove image link
        Then i can see the default image
        And i can still see the default image after page reload.
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)

        self.assert_default_image_has_public_access(profile_page)

        with self.verify_pref_change_event_during(
            username, user_id, 'profile_image_uploaded_at', table='auth_userprofile'
        ):
            profile_page.upload_file(filename='image.jpg')
        self.assertTrue(profile_page.image_upload_success)

        with self.verify_pref_change_event_during(
            username, user_id, 'profile_image_uploaded_at', table='auth_userprofile'
        ):
            self.assertTrue(profile_page.remove_profile_image())

        self.assertTrue(profile_page.profile_has_default_image)
        profile_page.visit()
        self.assertTrue(profile_page.profile_has_default_image)

    def test_user_cannot_remove_default_image(self):
        """
        Scenario: Remove profile image does not works for default images.

        Given that I am on my profile page with public access
        And I can see default image
        When I move my cursor to the image
        Then i can see only the upload image text
        And i cannot see the remove image text
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)

        self.assert_default_image_has_public_access(profile_page)
        self.assertFalse(profile_page.remove_link_present)

    def test_eventing_after_multiple_uploads(self):
        """
        Scenario: An event is fired when a user with a profile image uploads another image

        Given that I am on my profile page with public access
        And I upload a new image via file uploader
        When I upload another image via the file uploader
        Then two upload events have been emitted
        """
        username, user_id = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username, privacy=self.PRIVACY_PUBLIC)
        self.assert_default_image_has_public_access(profile_page)

        with self.verify_pref_change_event_during(
            username, user_id, 'profile_image_uploaded_at', table='auth_userprofile'
        ):
            profile_page.upload_file(filename='image.jpg')
        self.assertTrue(profile_page.image_upload_success)

        with self.verify_pref_change_event_during(
            username, user_id, 'profile_image_uploaded_at', table='auth_userprofile'
        ):
            profile_page.upload_file(filename='image.jpg', wait_for_upload_button=False)


@attr('shard_4')
class DifferentUserLearnerProfilePageTest(LearnerProfileTestMixin, WebAppTest):
    """
    Tests that verify viewing the profile page of a different user.
    """
    def test_different_user_private_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at a different user's private profile.

        Given that I am a registered user.
        And I visit a different user's private profile page.
        Then I shouldn't see the profile visibility selector dropdown.
        Then I see some of the profile fields are shown.
        """
        different_username, different_user_id = self.initialize_different_user(privacy=self.PRIVACY_PRIVATE)
        username, __ = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(different_username)
        self.verify_profile_page_is_private(profile_page, is_editable=False)
        self.verify_profile_page_view_event(username, different_user_id, visibility=self.PRIVACY_PRIVATE)

    def test_different_user_under_age(self):
        """
        Scenario: Verify that an under age user's profile is private to others.

        Given that I am a registered user.
        And I visit an under age user's profile page.
        Then I shouldn't see the profile visibility selector dropdown.
        Then I see that only the private fields are shown.
        """
        under_age_birth_year = datetime.now().year - 10
        different_username, different_user_id = self.initialize_different_user(
            privacy=self.PRIVACY_PUBLIC,
            birth_year=under_age_birth_year
        )
        username, __ = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(different_username)
        self.verify_profile_page_is_private(profile_page, is_editable=False)
        self.verify_profile_page_view_event(username, different_user_id, visibility=self.PRIVACY_PRIVATE)

    def test_different_user_public_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at a different user's public profile.

        Given that I am a registered user.
        And I visit a different user's public profile page.
        Then I shouldn't see the profile visibility selector dropdown.
        Then all the profile fields are shown.
        Then I shouldn't see the profile visibility selector dropdown.
        Also `location`, `language` and `about me` fields are not editable.
        """
        different_username, different_user_id = self.initialize_different_user(privacy=self.PRIVACY_PUBLIC)
        username, __ = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(different_username)
        profile_page.wait_for_public_fields()
        self.verify_profile_page_is_public(profile_page, is_editable=False)
        self.verify_profile_page_view_event(username, different_user_id, visibility=self.PRIVACY_PUBLIC)


@attr('a11y')
class LearnerProfileA11yTest(LearnerProfileTestMixin, WebAppTest):
    """
    Class to test learner profile accessibility.
    """

    def test_editable_learner_profile_a11y(self):
        """
        Test the accessibility of the editable version of the profile page
        (user viewing her own public profile).
        """
        username, _ = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username)

        profile_page.a11y_audit.config.set_rules({
            "ignore": [
                'skip-link',  # TODO: AC-179
                'link-href',  # TODO: AC-231
            ],
        })

        profile_page.a11y_audit.check_for_accessibility_errors()

        profile_page.make_field_editable('language_proficiencies')
        profile_page.a11y_audit.check_for_accessibility_errors()

        profile_page.make_field_editable('bio')
        profile_page.a11y_audit.check_for_accessibility_errors()

    def test_read_only_learner_profile_a11y(self):
        """
        Test the accessibility of the read-only version of a public profile page
        (user viewing someone else's profile page).
        """
        # initialize_different_user should cause country, language, and bio to be filled out (since
        # privacy is public). It doesn't appear that this is happening, although the method
        # works in regular bokchoy tests. Perhaps a problem with phantomjs? So this test is currently
        # only looking at a read-only profile page with a username.
        different_username, _ = self.initialize_different_user(privacy=self.PRIVACY_PUBLIC)
        self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(different_username)

        profile_page.a11y_audit.config.set_rules({
            "ignore": [
                'skip-link',  # TODO: AC-179
                'link-href',  # TODO: AC-231
            ],
        })

        profile_page.a11y_audit.check_for_accessibility_errors()

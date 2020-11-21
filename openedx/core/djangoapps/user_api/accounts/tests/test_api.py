# -*- coding: utf-8 -*-
"""
Unit tests for behavior that is specific to the api methods (vs. the view methods).
Most of the functionality is covered in test_views.py.
"""


import itertools
import unicodedata

import ddt
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from mock import Mock, patch
from six import iteritems
from social_django.models import UserSocialAuth
from common.djangoapps.student.models import (
    AccountRecovery,
    PendingEmailChange,
    PendingSecondaryEmailChange,
    UserProfile
)
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.student.tests.tests import UserSettingsEventTestMixin
from common.djangoapps.student.views.management import activate_secondary_email

from openedx.core.djangoapps.ace_common.tests.mixins import EmailTemplateTagMixin
from openedx.core.djangoapps.user_api.accounts import PRIVATE_VISIBILITY
from openedx.core.djangoapps.user_api.accounts.api import (
    get_account_settings,
    update_account_settings
)
from openedx.core.djangoapps.user_api.accounts.tests.retirement_helpers import (  # pylint: disable=unused-import
    RetirementTestCase,
    fake_requested_retirement,
    setup_retirement_states
)
from openedx.core.djangoapps.user_api.errors import (
    AccountUpdateError,
    AccountValidationError,
    UserNotAuthorized,
    UserNotFound
)
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.tests.factories import EnterpriseCustomerUserFactory


def mock_render_to_string(template_name, context):
    """Return a string that encodes template_name and context"""
    return str((template_name, sorted(iteritems(context))))


def mock_render_to_response(template_name):
    """
    Return an HttpResponse with content that encodes template_name and context
    """
    # This simulates any db access in the templates.
    UserProfile.objects.exists()
    return HttpResponse(template_name)


class CreateAccountMixin(object):
    def create_account(self, username, password, email):
        # pylint: disable=missing-docstring
        registration_url = reverse('user_api_registration')
        resp = self.client.post(registration_url, {
            'username': username,
            'email': email,
            'password': password,
            'name': username,
            'honor_code': 'true',
        })
        self.assertEqual(resp.status_code, 200)


@skip_unless_lms
@ddt.ddt
@patch('common.djangoapps.student.views.management.render_to_response', Mock(side_effect=mock_render_to_response, autospec=True))
class TestAccountApi(UserSettingsEventTestMixin, EmailTemplateTagMixin, CreateAccountMixin, RetirementTestCase):
    """
    These tests specifically cover the parts of the API methods that are not covered by test_views.py.
    This includes the specific types of error raised, and default behavior when optional arguments
    are not specified.
    """
    password = "test"

    def setUp(self):
        super(TestAccountApi, self).setUp()
        self.request_factory = RequestFactory()
        self.table = "student_languageproficiency"
        self.user = UserFactory.create(password=self.password)
        self.default_request = self.request_factory.get("/api/user/v1/accounts/")
        self.default_request.user = self.user
        self.different_user = UserFactory.create(password=self.password)
        self.staff_user = UserFactory(is_staff=True, password=self.password)
        self.reset_tracker()

        enterprise_patcher = patch('openedx.features.enterprise_support.api.enterprise_customer_for_request')
        enterprise_learner_patcher = enterprise_patcher.start()
        enterprise_learner_patcher.return_value = {}
        self.addCleanup(enterprise_learner_patcher.stop)

    def test_get_username_provided(self):
        """Test the difference in behavior when a username is supplied to get_account_settings."""
        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual(self.user.username, account_settings["username"])

        account_settings = get_account_settings(self.default_request, usernames=[self.user.username])[0]
        self.assertEqual(self.user.username, account_settings["username"])

        account_settings = get_account_settings(self.default_request, usernames=[self.different_user.username])[0]
        self.assertEqual(self.different_user.username, account_settings["username"])

    def test_get_configuration_provided(self):
        """Test the difference in behavior when a configuration is supplied to get_account_settings."""
        config = {
            "default_visibility": "private",
            "public_fields": [
                'email', 'name',
            ],
        }

        # With default configuration settings, email is not shared with other (non-staff) users.
        account_settings = get_account_settings(self.default_request, [self.different_user.username])[0]
        self.assertNotIn("email", account_settings)

        account_settings = get_account_settings(
            self.default_request,
            [self.different_user.username],
            configuration=config,
        )[0]
        self.assertEqual(self.different_user.email, account_settings["email"])

    def test_get_user_not_found(self):
        """Test that UserNotFound is thrown if there is no user with username."""
        with self.assertRaises(UserNotFound):
            get_account_settings(self.default_request, usernames=["does_not_exist"])

        self.user.username = "does_not_exist"
        request = self.request_factory.get("/api/user/v1/accounts/")
        request.user = self.user
        with self.assertRaises(UserNotFound):
            get_account_settings(request)

    def test_update_username_provided(self):
        """Test the difference in behavior when a username is supplied to update_account_settings."""
        update_account_settings(self.user, {"name": "Mickey Mouse"})
        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual("Mickey Mouse", account_settings["name"])

        update_account_settings(self.user, {"name": "Donald Duck"}, username=self.user.username)
        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual("Donald Duck", account_settings["name"])

        with self.assertRaises(UserNotAuthorized):
            update_account_settings(self.different_user, {"name": "Pluto"}, username=self.user.username)

    def test_update_non_existent_user(self):
        with self.assertRaises(UserNotAuthorized):
            update_account_settings(self.user, {}, username="does_not_exist")

        self.user.username = "does_not_exist"
        with self.assertRaises(UserNotFound):
            update_account_settings(self.user, {})

    def test_get_empty_social_links(self):
        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual(account_settings['social_links'], [])

    def test_set_single_social_link(self):
        social_links = [
            dict(platform="facebook", social_link="https://www.facebook.com/{}".format(self.user.username))
        ]
        update_account_settings(self.user, {"social_links": social_links})
        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual(account_settings['social_links'], social_links)

    def test_set_multiple_social_links(self):
        social_links = [
            dict(platform="facebook", social_link="https://www.facebook.com/{}".format(self.user.username)),
            dict(platform="twitter", social_link="https://www.twitter.com/{}".format(self.user.username)),
        ]
        update_account_settings(self.user, {"social_links": social_links})
        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual(account_settings['social_links'], social_links)

    def test_add_social_links(self):
        original_social_links = [
            dict(platform="facebook", social_link="https://www.facebook.com/{}".format(self.user.username))
        ]
        update_account_settings(self.user, {"social_links": original_social_links})

        extra_social_links = [
            dict(platform="twitter", social_link="https://www.twitter.com/{}".format(self.user.username)),
            dict(platform="linkedin", social_link="https://www.linkedin.com/in/{}".format(self.user.username)),
        ]
        update_account_settings(self.user, {"social_links": extra_social_links})

        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual(
            account_settings['social_links'],
            sorted(original_social_links + extra_social_links, key=lambda s: s['platform']),
        )

    def test_replace_social_links(self):
        original_facebook_link = dict(platform="facebook", social_link="https://www.facebook.com/myself")
        original_twitter_link = dict(platform="twitter", social_link="https://www.twitter.com/myself")
        update_account_settings(self.user, {"social_links": [original_facebook_link, original_twitter_link]})

        modified_facebook_link = dict(platform="facebook", social_link="https://www.facebook.com/new_me")
        update_account_settings(self.user, {"social_links": [modified_facebook_link]})

        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual(account_settings['social_links'], [modified_facebook_link, original_twitter_link])

    def test_remove_social_link(self):
        original_facebook_link = dict(platform="facebook", social_link="https://www.facebook.com/myself")
        original_twitter_link = dict(platform="twitter", social_link="https://www.twitter.com/myself")
        update_account_settings(self.user, {"social_links": [original_facebook_link, original_twitter_link]})

        removed_facebook_link = dict(platform="facebook", social_link="")
        update_account_settings(self.user, {"social_links": [removed_facebook_link]})

        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual(account_settings['social_links'], [original_twitter_link])

    def test_unsupported_social_link_platform(self):
        social_links = [
            dict(platform="unsupported", social_link="https://www.unsupported.com/{}".format(self.user.username))
        ]
        with self.assertRaises(AccountValidationError):
            update_account_settings(self.user, {"social_links": social_links})

    def test_update_success_for_enterprise(self):
        EnterpriseCustomerUserFactory(user_id=self.user.id)
        level_of_education = "m"
        successful_update = {
            "level_of_education": level_of_education,
        }
        update_account_settings(self.user, successful_update)
        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual(level_of_education, account_settings["level_of_education"])

    @patch('openedx.features.enterprise_support.api.enterprise_customer_for_request')
    @patch('openedx.features.enterprise_support.utils.third_party_auth.provider.Registry.get')
    @ddt.data(
        *itertools.product(
            # field_name_value values
            (("email", "new_email@example.com"), ("name", "new name"), ("country", "IN")),
            # is_enterprise_user
            (True, False),
            # is_synch_learner_profile_data
            (True, False),
            # has `UserSocialAuth` record
            (True, False),
        )
    )
    @ddt.unpack
    def test_update_validation_error_for_enterprise(
        self,
        field_name_value,
        is_enterprise_user,
        is_synch_learner_profile_data,
        has_user_social_auth_record,
        mock_auth_provider,
        mock_customer,
    ):
        idp_backend_name = 'tpa-saml'
        mock_customer.return_value = {}
        if is_enterprise_user:
            mock_customer.return_value.update({
                'uuid': 'real-ent-uuid',
                'name': 'Dummy Enterprise',
                'identity_provider': 'saml-ubc'
            })
        mock_auth_provider.return_value.sync_learner_profile_data = is_synch_learner_profile_data
        mock_auth_provider.return_value.backend_name = idp_backend_name

        update_data = {field_name_value[0]: field_name_value[1]}

        user_fullname_editable = False
        if has_user_social_auth_record:
            UserSocialAuth.objects.create(
                provider=idp_backend_name,
                user=self.user
            )
        else:
            UserSocialAuth.objects.all().delete()
            # user's fullname is editable if no `UserSocialAuth` record exists
            user_fullname_editable = field_name_value[0] == 'name'

        # prevent actual email change requests
        with patch('openedx.core.djangoapps.user_api.accounts.api.student_views.do_email_change_request'):
            # expect field un-editability only when all of the following conditions are met
            if is_enterprise_user and is_synch_learner_profile_data and not user_fullname_editable:
                with self.assertRaises(AccountValidationError) as validation_error:
                    update_account_settings(self.user, update_data)
                    field_errors = validation_error.exception.field_errors
                    self.assertEqual(
                        "This field is not editable via this API",
                        field_errors[field_name_value[0]]["developer_message"],
                    )
            else:
                update_account_settings(self.user, update_data)
                account_settings = get_account_settings(self.default_request)[0]
                if field_name_value[0] != "email":
                    self.assertEqual(field_name_value[1], account_settings[field_name_value[0]])

    def test_update_error_validating(self):
        """Test that AccountValidationError is thrown if incorrect values are supplied."""
        with self.assertRaises(AccountValidationError):
            update_account_settings(self.user, {"username": "not_allowed"})

        with self.assertRaises(AccountValidationError):
            update_account_settings(self.user, {"gender": "undecided"})

        with self.assertRaises(AccountValidationError):
            update_account_settings(
                self.user,
                {"profile_image": {"has_image": "not_allowed", "image_url": "not_allowed"}}
            )

        # Check the various language_proficiencies validation failures.
        # language_proficiencies must be a list of dicts, each containing a
        # unique 'code' key representing the language code.
        with self.assertRaises(AccountValidationError):
            update_account_settings(
                self.user,
                {"language_proficiencies": "not_a_list"}
            )
        with self.assertRaises(AccountValidationError):
            update_account_settings(
                self.user,
                {"language_proficiencies": [{}]}
            )

        with self.assertRaises(AccountValidationError):
            update_account_settings(self.user, {"account_privacy": ""})

    def test_update_multiple_validation_errors(self):
        """Test that all validation errors are built up and returned at once"""
        # Send a read-only error, serializer error, and email validation error.

        naughty_update = {
            "username": "not_allowed",
            "gender": "undecided",
            "email": "not an email address",
            "name": "<p style=\"font-size:300px; color:green;\"></br>Name<input type=\"text\"></br>Content spoof"
        }

        with self.assertRaises(AccountValidationError) as context_manager:
            update_account_settings(self.user, naughty_update)
        field_errors = context_manager.exception.field_errors
        self.assertEqual(4, len(field_errors))
        self.assertEqual("This field is not editable via this API", field_errors["username"]["developer_message"])
        self.assertIn(
            "Value \'undecided\' is not valid for field \'gender\'",
            field_errors["gender"]["developer_message"]
        )
        self.assertIn("Valid e-mail address required.", field_errors["email"]["developer_message"])
        self.assertIn("Full Name cannot contain the following characters: < >", field_errors["name"]["user_message"])

    @patch('django.core.mail.EmailMultiAlternatives.send')
    @patch('common.djangoapps.student.views.management.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_update_sending_email_fails(self, send_mail):
        """Test what happens if all validation checks pass, but sending the email for email change fails."""
        send_mail.side_effect = [Exception, None]
        less_naughty_update = {
            "name": "Mickey Mouse",
            "email": "seems_ok@sample.com"
        }

        with patch('crum.get_current_request', return_value=self.fake_request):
            with self.assertRaises(AccountUpdateError) as context_manager:
                update_account_settings(self.user, less_naughty_update)
        self.assertIn("Error thrown from do_email_change_request", context_manager.exception.developer_message)

        # Verify that the name change happened, even though the attempt to send the email failed.
        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual("Mickey Mouse", account_settings["name"])

    @patch.dict(settings.FEATURES, dict(ALLOW_EMAIL_ADDRESS_CHANGE=False))
    def test_email_changes_disabled(self):
        """
        Test that email address changes are rejected when ALLOW_EMAIL_ADDRESS_CHANGE is not set.
        """
        disabled_update = {"email": "valid@example.com"}

        with self.assertRaises(AccountUpdateError) as context_manager:
            update_account_settings(self.user, disabled_update)
        self.assertIn("Email address changes have been disabled", context_manager.exception.developer_message)

    @patch.dict(settings.FEATURES, dict(ALLOW_EMAIL_ADDRESS_CHANGE=True))
    def test_email_changes_blocked_on_retired_email(self):
        """
        Test that email address changes are rejected when an email associated with a *partially* retired account is
        specified.
        """
        # First, record the original email addres of the primary user (the one seeking to update their email).
        original_email = self.user.email

        # Setup a partially retired user.  This user recently submitted a deletion request, but it has not been
        # processed yet.
        partially_retired_email = 'partially_retired@example.com'
        partially_retired_user = UserFactory(email=partially_retired_email)
        fake_requested_retirement(partially_retired_user)

        # Attempt to change email to the one of the partially retired user.
        rejected_update = {'email': partially_retired_email}
        update_account_settings(self.user, rejected_update)

        # No error should be thrown, and we need to check that the email update was skipped.
        assert self.user.email == original_email

    @patch('openedx.core.djangoapps.user_api.accounts.serializers.AccountUserSerializer.save')
    def test_serializer_save_fails(self, serializer_save):
        """
        Test the behavior of one of the serializers failing to save. Note that email request change
        won't be processed in this case.
        """
        serializer_save.side_effect = [Exception, None]
        update_will_fail = {
            "name": "Mickey Mouse",
            "email": "ok@sample.com"
        }

        with self.assertRaises(AccountUpdateError) as context_manager:
            update_account_settings(self.user, update_will_fail)
        self.assertIn("Error thrown when saving account updates", context_manager.exception.developer_message)

        # Verify that no email change request was initiated.
        pending_change = PendingEmailChange.objects.filter(user=self.user)
        self.assertEqual(0, len(pending_change))

    def test_language_proficiency_eventing(self):
        """
        Test that eventing of language proficiencies, which happens update_account_settings method, behaves correctly.
        """
        def verify_event_emitted(new_value, old_value):
            """
            Confirm that the user setting event was properly emitted
            """
            update_account_settings(self.user, {"language_proficiencies": new_value})
            self.assert_user_setting_event_emitted(setting='language_proficiencies', old=old_value, new=new_value)
            self.reset_tracker()

        # Change language_proficiencies and verify events are fired.
        verify_event_emitted([{"code": "en"}], [])
        verify_event_emitted([{"code": "en"}, {"code": "fr"}], [{"code": "en"}])
        # Note that events are fired even if there has been no actual change.
        verify_event_emitted([{"code": "en"}, {"code": "fr"}], [{"code": "en"}, {"code": "fr"}])
        verify_event_emitted([], [{"code": "en"}, {"code": "fr"}])

    def test_add_account_recovery(self):
        test_email = "test@example.com"
        pending_secondary_email_changes = PendingSecondaryEmailChange.objects.filter(user=self.user)
        self.assertEqual(0, len(pending_secondary_email_changes))

        account_recovery_objects = AccountRecovery.objects.filter(user=self.user)
        self.assertEqual(0, len(account_recovery_objects))

        with patch('crum.get_current_request', return_value=self.fake_request):
            update = {"secondary_email": test_email}
            update_account_settings(self.user, update)

        pending_secondary_email_change = PendingSecondaryEmailChange.objects.get(user=self.user)
        self.assertIsNot(pending_secondary_email_change, None)
        self.assertEqual(pending_secondary_email_change.new_secondary_email, test_email)

        activate_secondary_email(self.fake_request, pending_secondary_email_change.activation_key)

        pending_secondary_email_changes = PendingSecondaryEmailChange.objects.filter(user=self.user)
        self.assertEqual(0, len(pending_secondary_email_changes))

        account_recovery = AccountRecovery.objects.get(user=self.user)
        self.assertIsNot(account_recovery, None)
        self.assertEqual(account_recovery.secondary_email, test_email)

    def test_change_country_removes_state(self):
        '''
        Test that changing the country (to something other than a country with
        states) removes the state
        '''
        # First set the country and state
        update_account_settings(self.user, {"country": UserProfile.COUNTRY_WITH_STATES, "state": "MA"})
        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual(account_settings['country'], UserProfile.COUNTRY_WITH_STATES)
        self.assertEqual(account_settings['state'], 'MA')

        # Change the country and check that state is removed
        update_account_settings(self.user, {"country": ""})
        account_settings = get_account_settings(self.default_request)[0]
        self.assertEqual(account_settings['country'], None)
        self.assertEqual(account_settings['state'], None)


@patch('openedx.core.djangoapps.user_api.accounts.image_helpers._PROFILE_IMAGE_SIZES', [50, 10])
@patch.dict(
    'django.conf.settings.PROFILE_IMAGE_SIZES_MAP',
    {'full': 50, 'small': 10},
    clear=True
)
@skip_unless_lms
class AccountSettingsOnCreationTest(CreateAccountMixin, TestCase):
    # pylint: disable=missing-docstring

    USERNAME = u'frank-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'frank+underwood@example.com'

    def test_create_account(self):
        # Create a new account, which should have empty account settings by default.
        self.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        # Retrieve the account settings
        user = User.objects.get(username=self.USERNAME)
        request = RequestFactory().get("/api/user/v1/accounts/")
        request.user = user
        account_settings = get_account_settings(request)[0]

        # Expect a date joined field but remove it to simplify the following comparison
        self.assertIsNotNone(account_settings['date_joined'])
        del account_settings['date_joined']

        # Expect all the values to be defaulted
        self.assertEqual(account_settings, {
            'username': self.USERNAME,
            'email': self.EMAIL,
            'name': self.USERNAME,
            'gender': None,
            'goals': u'',
            'is_active': False,
            'level_of_education': None,
            'mailing_address': u'',
            'year_of_birth': None,
            'country': None,
            'state': None,
            'social_links': [],
            'bio': None,
            'profile_image': {
                'has_image': False,
                'image_url_full': request.build_absolute_uri('/static/default_50.png'),
                'image_url_small': request.build_absolute_uri('/static/default_10.png'),
            },
            'requires_parental_consent': True,
            'language_proficiencies': [],
            'account_privacy': PRIVATE_VISIBILITY,
            'accomplishments_shared': False,
            'extended_profile': [],
            'secondary_email': None,
            'secondary_email_enabled': None,
            'time_zone': None,
            'course_certificates': None,
            'phone_number': None,
        })

    def test_normalize_password(self):
        """
        Test that unicode normalization on passwords is happening when a user is created.
        """
        # Set user password to NFKD format so that we can test that it is normalized to
        # NFKC format upon account creation.
        self.create_account(self.USERNAME, unicodedata.normalize('NFKD', u'Ṗŕệṿïệẅ Ṯệẍt'), self.EMAIL)

        user = User.objects.get(username=self.USERNAME)

        salt_val = user.password.split('$')[1]

        expected_user_password = make_password(unicodedata.normalize('NFKC', u'Ṗŕệṿïệẅ Ṯệẍt'), salt_val)
        self.assertEqual(expected_user_password, user.password)

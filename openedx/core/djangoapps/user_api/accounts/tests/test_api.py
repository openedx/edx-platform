# -*- coding: utf-8 -*-
"""
Unit tests for behavior that is specific to the api methods (vs. the view methods).
Most of the functionality is covered in test_views.py.
"""

import re
import unicodedata

import ddt
import pytest
from dateutil.parser import parse as parse_datetime
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.test.client import RequestFactory
from mock import Mock, patch
from six import iteritems

from openedx.core.djangoapps.ace_common.tests.mixins import EmailTemplateTagMixin
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.user_api.accounts import PRIVATE_VISIBILITY, USERNAME_MAX_LENGTH
from openedx.core.djangoapps.user_api.accounts.api import (
    activate_account,
    create_account,
    get_account_settings,
    request_password_change,
    update_account_settings
)
from openedx.core.djangoapps.user_api.accounts.tests.retirement_helpers import (  # pylint: disable=unused-import
    RetirementTestCase,
    fake_requested_retirement,
    setup_retirement_states
)
from openedx.core.djangoapps.user_api.accounts.tests.testutils import (
    INVALID_EMAILS,
    INVALID_PASSWORDS,
    INVALID_USERNAMES,
    VALID_USERNAMES_UNICODE
)
from openedx.core.djangoapps.user_api.config.waffle import (
    PREVENT_AUTH_USER_WRITES,
    SYSTEM_MAINTENANCE_MSG,
    waffle
)
from openedx.core.djangoapps.user_api.errors import (
    AccountEmailInvalid,
    AccountPasswordInvalid,
    AccountRequestError,
    AccountUpdateError,
    AccountUserAlreadyExists,
    AccountUsernameInvalid,
    AccountValidationError,
    UserAPIInternalError,
    UserNotAuthorized,
    UserNotFound
)
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.core.lib.tests import attr
from student.models import PendingEmailChange
from student.tests.factories import UserFactory
from student.tests.tests import UserSettingsEventTestMixin


def mock_render_to_string(template_name, context):
    """Return a string that encodes template_name and context"""
    return str((template_name, sorted(iteritems(context))))


@attr(shard=2)
@skip_unless_lms
class TestAccountApi(UserSettingsEventTestMixin, EmailTemplateTagMixin, RetirementTestCase):
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

            "shareable_fields": [
                'name',
            ],

            "public_fields": [
                'email',
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

    def test_update_user_not_found(self):
        """Test that UserNotFound is thrown if there is no user with username."""
        with self.assertRaises(UserNotFound):
            update_account_settings(self.user, {}, username="does_not_exist")

        self.user.username = "does_not_exist"
        with self.assertRaises(UserNotFound):
            update_account_settings(self.user, {})

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

    @patch('django.core.mail.send_mail')
    @patch('student.views.management.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
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


@attr(shard=2)
@patch('openedx.core.djangoapps.user_api.accounts.image_helpers._PROFILE_IMAGE_SIZES', [50, 10])
@patch.dict(
    'django.conf.settings.PROFILE_IMAGE_SIZES_MAP',
    {'full': 50, 'small': 10},
    clear=True
)
@skip_unless_lms
class AccountSettingsOnCreationTest(TestCase):
    # pylint: disable=missing-docstring

    USERNAME = u'frank-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'frank+underwood@example.com'

    def test_create_account(self):
        # Create a new account, which should have empty account settings by default.
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
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
            'name': u'',
            'gender': None,
            'goals': None,
            'is_active': False,
            'level_of_education': None,
            'mailing_address': None,
            'year_of_birth': None,
            'country': None,
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
            'secondary_email': None
        })

    def test_normalize_password(self):
        """
        Test that unicode normalization on passwords is happening when a user is created.
        """
        # Set user password to NFKD format so that we can test that it is normalized to
        # NFKC format upon account creation.
        create_account(self.USERNAME, unicodedata.normalize('NFKD', u'Ṗŕệṿïệẅ Ṯệẍt'), self.EMAIL)

        user = User.objects.get(username=self.USERNAME)

        salt_val = user.password.split('$')[1]

        expected_user_password = make_password(unicodedata.normalize('NFKC', u'Ṗŕệṿïệẅ Ṯệẍt'), salt_val)
        self.assertEqual(expected_user_password, user.password)


@attr(shard=2)
@pytest.mark.django_db
def test_create_account_duplicate_email(django_db_use_migrations):
    """
    Test case for duplicate email constraint
    Email uniqueness constraints were introduced in a database migration,
    which we disable in the unit tests to improve the speed of the test suite

    This test only runs if migrations have been run.

    django_db_use_migrations is a pytest_django fixture which tells us whether
    migrations are being used.
    """
    password = 'legit'
    email = 'zappadappadoo@example.com'

    if django_db_use_migrations:
        create_account('zappadappadoo', password, email)

        with pytest.raises(
                AccountUserAlreadyExists,
                message='Migrations are being used, but creating an account with duplicate email succeeded!'
        ):
            create_account('different_user', password, email)


@attr(shard=2)
@ddt.ddt
class AccountCreationActivationAndPasswordChangeTest(TestCase):
    """
    Test cases to cover the account initialization workflow
    """
    USERNAME = u'claire-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'claire+underwood@example.com'

    IS_SECURE = False

    @skip_unless_lms
    def test_activate_account(self):
        # Create the account, which is initially inactive
        activation_key = create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        user = User.objects.get(username=self.USERNAME)

        request = RequestFactory().get("/api/user/v1/accounts/")
        request.user = user
        account = get_account_settings(request)[0]
        self.assertEqual(self.USERNAME, account["username"])
        self.assertEqual(self.EMAIL, account["email"])
        self.assertFalse(account["is_active"])

        # Activate the account and verify that it is now active
        activate_account(activation_key)
        account = get_account_settings(request)[0]
        self.assertTrue(account['is_active'])

    def test_create_account_duplicate_username(self):
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        with self.assertRaises(AccountUserAlreadyExists):
            create_account(self.USERNAME, self.PASSWORD, 'different+email@example.com')

    def test_username_too_long(self):
        long_username = 'e' * (USERNAME_MAX_LENGTH + 1)
        with self.assertRaises(AccountUsernameInvalid):
            create_account(long_username, self.PASSWORD, self.EMAIL)

    @ddt.data(*INVALID_EMAILS)
    def test_create_account_invalid_email(self, invalid_email):
        with pytest.raises(AccountEmailInvalid):
            create_account(self.USERNAME, self.PASSWORD, invalid_email)

    @ddt.data(*INVALID_PASSWORDS)
    def test_create_account_invalid_password(self, invalid_password):
        with pytest.raises(AccountPasswordInvalid):
            create_account(self.USERNAME, invalid_password, self.EMAIL)

    def test_create_account_username_password_equal(self):
        # Username and password cannot be the same
        with pytest.raises(AccountPasswordInvalid):
            create_account(self.USERNAME, self.USERNAME, self.EMAIL)

    @ddt.data(*INVALID_USERNAMES)
    def test_create_account_invalid_username(self, invalid_username):
        with pytest.raises(AccountRequestError):
            create_account(invalid_username, self.PASSWORD, self.EMAIL)

    def test_create_account_prevent_auth_user_writes(self):
        with pytest.raises(UserAPIInternalError, message=SYSTEM_MAINTENANCE_MSG):
            with waffle().override(PREVENT_AUTH_USER_WRITES, True):
                create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

    def test_activate_account_invalid_key(self):
        with pytest.raises(UserNotAuthorized):
            activate_account(u'invalid')

    def test_activate_account_prevent_auth_user_writes(self):
        activation_key = create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        with pytest.raises(UserAPIInternalError, message=SYSTEM_MAINTENANCE_MSG):
            with waffle().override(PREVENT_AUTH_USER_WRITES, True):
                activate_account(activation_key)

    @skip_unless_lms
    def test_request_password_change(self):
        # Create and activate an account
        activation_key = create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        activate_account(activation_key)

        request = RequestFactory().post('/password')
        request.user = Mock()
        request.site = SiteFactory()

        with patch('crum.get_current_request', return_value=request):
            # Request a password change
            request_password_change(self.EMAIL, self.IS_SECURE)

        # Verify that one email message has been sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the body of the message contains something that looks
        # like an activation link
        email_body = mail.outbox[0].body
        result = re.search(r'(?P<url>https?://[^\s]+)', email_body)
        self.assertIsNot(result, None)

    @skip_unless_lms
    def test_request_password_change_invalid_user(self):
        with self.assertRaises(UserNotFound):
            request_password_change(self.EMAIL, self.IS_SECURE)

        # Verify that no email messages have been sent
        self.assertEqual(len(mail.outbox), 0)

    @skip_unless_lms
    def test_request_password_change_inactive_user(self):
        # Create an account, but do not activate it
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        request = RequestFactory().post('/password')
        request.user = Mock()
        request.site = SiteFactory()

        with patch('crum.get_current_request', return_value=request):
            request_password_change(self.EMAIL, self.IS_SECURE)

        # Verify that the activation email was still sent
        self.assertEqual(len(mail.outbox), 1)

    def _assert_is_datetime(self, timestamp):
        """
        Internal helper to validate the type of the provided timestamp
        """
        if not timestamp:
            return False
        try:
            parse_datetime(timestamp)
        except ValueError:
            return False
        else:
            return True

    @patch("openedx.core.djangoapps.site_configuration.helpers.get_value", Mock(return_value=False))
    def test_create_account_not_allowed(self):
        """
        Test case to check user creation is forbidden when ALLOW_PUBLIC_ACCOUNT_CREATION feature flag is turned off
        """
        response = create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        self.assertEqual(response.status_code, 403)


@attr(shard=2)
@ddt.ddt
class AccountCreationUnicodeUsernameTest(TestCase):
    """
    Test cases to cover the account initialization workflow
    """
    PASSWORD = u'unicode-user-password'
    EMAIL = u'unicode-user-username@example.com'

    @ddt.data(*VALID_USERNAMES_UNICODE)
    def test_unicode_usernames(self, unicode_username):
        with patch.dict(settings.FEATURES, {'ENABLE_UNICODE_USERNAME': False}):
            with self.assertRaises(AccountUsernameInvalid):
                create_account(unicode_username, self.PASSWORD, self.EMAIL)  # Feature is disabled, therefore invalid.

        with patch.dict(settings.FEATURES, {'ENABLE_UNICODE_USERNAME': True}):
            try:
                create_account(unicode_username, self.PASSWORD, self.EMAIL)
            except AccountUsernameInvalid:
                self.fail(u'The API should accept Unicode username `{unicode_username}`.'.format(
                    unicode_username=unicode_username,
                ))

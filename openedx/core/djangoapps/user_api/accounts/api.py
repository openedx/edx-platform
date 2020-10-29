# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
"""
Programmatic integration point for User API Accounts sub-application
"""


import datetime

import six
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import ValidationError, validate_email
from django.utils.translation import override as override_language
from django.utils.translation import ugettext as _
from pytz import UTC
from six import text_type  # pylint: disable=ungrouped-imports
from common.djangoapps.student import views as student_views
from common.djangoapps.student.models import (
    AccountRecovery,
    User,
    UserProfile,
    email_exists_or_retired,
    username_exists_or_retired
)
from common.djangoapps.util.model_utils import emit_setting_changed_event
from common.djangoapps.util.password_policy_validators import validate_password

from openedx.core.djangoapps.user_api import accounts, errors, helpers
from openedx.core.djangoapps.user_api.errors import (
    AccountUpdateError,
    AccountValidationError,
    PreferenceValidationError
)
from openedx.core.djangoapps.user_api.preferences.api import update_user_preferences
from openedx.core.djangoapps.user_authn.views.registration_form import validate_name, validate_username
from openedx.core.lib.api.view_utils import add_serializer_errors
from openedx.features.enterprise_support.utils import get_enterprise_readonly_account_fields
from .serializers import AccountLegacyProfileSerializer, AccountUserSerializer, UserReadOnlySerializer, _visible_fields

# Public access point for this function.
visible_fields = _visible_fields


@helpers.intercept_errors(errors.UserAPIInternalError, ignore_errors=[errors.UserAPIRequestError])
def get_account_settings(request, usernames=None, configuration=None, view=None):
    """Returns account information for a user serialized as JSON.

    Note:
        If `request.user.username` != `username`, this method will return differing amounts of information
        based on who `request.user` is and the privacy settings of the user associated with `username`.

    Args:
        request (Request): The request object with account information about the requesting user.
            Only the user with username `username` or users with "is_staff" privileges can get full
            account information. Other users will get the account fields that the user has elected to share.
        usernames (list): Optional list of usernames for the desired account information. If not
            specified, `request.user.username` is assumed.
        configuration (dict): an optional configuration specifying which fields in the account
            can be shared, and the default visibility settings. If not present, the setting value with
            key ACCOUNT_VISIBILITY_CONFIGURATION is used.
        view (str): An optional string allowing "is_staff" users and users requesting their own
            account information to get just the fields that are shared with everyone. If view is
            "shared", only shared account information will be returned, regardless of `request.user`.

    Returns:
         A list of users account details.

    Raises:
         errors.UserNotFound: no user with username `username` exists (or `request.user.username` if
            `username` is not specified)
         errors.UserAPIInternalError: the operation failed due to an unexpected error.

    """
    requesting_user = request.user
    usernames = usernames or [requesting_user.username]

    requested_users = User.objects.select_related('profile').filter(username__in=usernames)
    if not requested_users:
        raise errors.UserNotFound()

    serialized_users = []
    for user in requested_users:
        has_full_access = requesting_user.is_staff or requesting_user.username == user.username
        if has_full_access and view != 'shared':
            admin_fields = settings.ACCOUNT_VISIBILITY_CONFIGURATION.get('admin_fields')
        else:
            admin_fields = None
        serialized_users.append(UserReadOnlySerializer(
            user,
            configuration=configuration,
            custom_fields=admin_fields,
            context={'request': request}
        ).data)

    return serialized_users


@helpers.intercept_errors(errors.UserAPIInternalError, ignore_errors=[errors.UserAPIRequestError])
def update_account_settings(requesting_user, update, username=None):
    """Update user account information.

    Note:
        It is up to the caller of this method to enforce the contract that this method is only called
        with the user who made the request.

    Arguments:
        requesting_user (User): The user requesting to modify account information. Only the user with username
            'username' has permissions to modify account information.
        update (dict): The updated account field values.
        username (str): Optional username specifying which account should be updated. If not specified,
            `requesting_user.username` is assumed.

    Raises:
        errors.UserNotFound: no user with username `username` exists (or `requesting_user.username` if
            `username` is not specified)
        errors.UserNotAuthorized: the requesting_user does not have access to change the account
            associated with `username`
        errors.AccountValidationError: the update was not attempted because validation errors were found with
            the supplied update
        errors.AccountUpdateError: the update could not be completed. Note that if multiple fields are updated at the
            same time, some parts of the update may have been successful, even if an errors.AccountUpdateError is
            returned; in particular, the user account (not including e-mail address) may have successfully been updated,
            but then the e-mail change request, which is processed last, may throw an error.
        errors.UserAPIInternalError: the operation failed due to an unexpected error.

    """
    # Get user
    if username is None:
        username = requesting_user.username
    if requesting_user.username != username:
        raise errors.UserNotAuthorized()
    user, user_profile = _get_user_and_profile(username)

    # Validate fields to update
    field_errors = {}
    _validate_read_only_fields(user, update, field_errors)

    user_serializer = AccountUserSerializer(user, data=update)
    legacy_profile_serializer = AccountLegacyProfileSerializer(user_profile, data=update)
    for serializer in user_serializer, legacy_profile_serializer:
        add_serializer_errors(serializer, update, field_errors)

    _validate_email_change(user, update, field_errors)
    _validate_secondary_email(user, update, field_errors)
    old_name = _validate_name_change(user_profile, update, field_errors)
    old_language_proficiencies = _get_old_language_proficiencies_if_updating(user_profile, update)

    if field_errors:
        raise errors.AccountValidationError(field_errors)

    # Save requested changes
    try:
        for serializer in user_serializer, legacy_profile_serializer:
            serializer.save()

        _update_preferences_if_needed(update, requesting_user, user)
        _notify_language_proficiencies_update_if_needed(update, user, user_profile, old_language_proficiencies)
        _store_old_name_if_needed(old_name, user_profile, requesting_user)
        _update_extended_profile_if_needed(update, user_profile)
        _update_state_if_needed(update, user_profile)

    except PreferenceValidationError as err:
        raise AccountValidationError(err.preference_errors)
    except (AccountUpdateError, AccountValidationError) as err:
        raise err
    except Exception as err:
        raise AccountUpdateError(
            u"Error thrown when saving account updates: '{}'".format(text_type(err))
        )

    _send_email_change_requests_if_needed(update, user)


def _validate_read_only_fields(user, data, field_errors):
    # Check for fields that are not editable. Marking them read-only causes them to be ignored, but we wish to 400.
    read_only_fields = set(data.keys()).intersection(
        # Remove email since it is handled separately below when checking for changing_email.
        (set(AccountUserSerializer.get_read_only_fields()) - set(["email"])) |
        set(AccountLegacyProfileSerializer.get_read_only_fields() or set()) |
        get_enterprise_readonly_account_fields(user)
    )

    for read_only_field in read_only_fields:
        field_errors[read_only_field] = {
            "developer_message": u"This field is not editable via this API",
            "user_message": _(u"The '{field_name}' field cannot be edited.").format(field_name=read_only_field)
        }
        del data[read_only_field]


def _validate_email_change(user, data, field_errors):
    # If user has requested to change email, we must call the multi-step process to handle this.
    # It is not handled by the serializer (which considers email to be read-only).
    if "email" not in data:
        return

    if not settings.FEATURES['ALLOW_EMAIL_ADDRESS_CHANGE']:
        raise AccountUpdateError(u"Email address changes have been disabled by the site operators.")

    new_email = data["email"]
    try:
        student_views.validate_new_email(user, new_email)
    except ValueError as err:
        field_errors["email"] = {
            "developer_message": u"Error thrown from validate_new_email: '{}'".format(text_type(err)),
            "user_message": text_type(err)
        }
        return

    # Don't process with sending email to given new email, if it is already associated with
    # an account. User must see same success message with no error.
    # This is so that this endpoint cannot be used to determine if an email is valid or not.
    if email_exists_or_retired(new_email):
        del data["email"]


def _validate_secondary_email(user, data, field_errors):
    if "secondary_email" not in data:
        return

    secondary_email = data["secondary_email"]

    try:
        student_views.validate_secondary_email(user, secondary_email)
    except ValueError as err:
        field_errors["secondary_email"] = {
            "developer_message": u"Error thrown from validate_secondary_email: '{}'".format(text_type(err)),
            "user_message": text_type(err)
        }
    else:
        # Don't process with sending email to given new email, if it is already associated with
        # an account. User must see same success message with no error.
        # This is so that this endpoint cannot be used to determine if an email is valid or not.
        if email_exists_or_retired(secondary_email):
            del data["secondary_email"]


def _validate_name_change(user_profile, data, field_errors):
    # If user has requested to change name, store old name because we must update associated metadata
    # after the save process is complete.
    if "name" not in data:
        return None

    old_name = user_profile.name
    try:
        validate_name(data['name'])
    except ValidationError as err:
        field_errors["name"] = {
            "developer_message": u"Error thrown from validate_name: '{}'".format(err.message),
            "user_message": err.message
        }
        return None

    return old_name


def _get_old_language_proficiencies_if_updating(user_profile, data):
    if "language_proficiencies" in data:
        return list(user_profile.language_proficiencies.values('code'))


def _update_preferences_if_needed(data, requesting_user, user):
    if 'account_privacy' in data:
        update_user_preferences(
            requesting_user, {'account_privacy': data["account_privacy"]}, user
        )


def _notify_language_proficiencies_update_if_needed(data, user, user_profile, old_language_proficiencies):
    if "language_proficiencies" in data:
        new_language_proficiencies = data["language_proficiencies"]
        emit_setting_changed_event(
            user=user,
            db_table=user_profile.language_proficiencies.model._meta.db_table,
            setting_name="language_proficiencies",
            old_value=old_language_proficiencies,
            new_value=new_language_proficiencies,
        )


def _update_extended_profile_if_needed(data, user_profile):
    if 'extended_profile' in data:
        meta = user_profile.get_meta()
        new_extended_profile = data['extended_profile']
        for field in new_extended_profile:
            field_name = field['field_name']
            new_value = field['field_value']
            meta[field_name] = new_value
        user_profile.set_meta(meta)
        user_profile.save()


def _update_state_if_needed(data, user_profile):
    # If the country was changed to something other than US, remove the state.
    if "country" in data and data['country'] != UserProfile.COUNTRY_WITH_STATES:
        user_profile.state = None
        user_profile.save()


def _store_old_name_if_needed(old_name, user_profile, requesting_user):
    # If the name was changed, store information about the change operation. This is outside of the
    # serializer so that we can store who requested the change.
    if old_name:
        meta = user_profile.get_meta()
        if 'old_names' not in meta:
            meta['old_names'] = []
        meta['old_names'].append([
            old_name,
            u"Name change requested through account API by {0}".format(requesting_user.username),
            datetime.datetime.now(UTC).isoformat()
        ])
        user_profile.set_meta(meta)
        user_profile.save()


def _send_email_change_requests_if_needed(data, user):
    new_email = data.get("email")
    if new_email:
        try:
            student_views.do_email_change_request(user, new_email)
        except ValueError as err:
            raise AccountUpdateError(
                u"Error thrown from do_email_change_request: '{}'".format(text_type(err)),
                user_message=text_type(err)
            )

    new_secondary_email = data.get("secondary_email")
    if new_secondary_email:
        try:
            student_views.do_email_change_request(
                user=user,
                new_email=new_secondary_email,
                secondary_email_change_request=True,
            )
        except ValueError as err:
            raise AccountUpdateError(
                u"Error thrown from do_email_change_request: '{}'".format(text_type(err)),
                user_message=text_type(err)
            )


def get_name_validation_error(name):
    """Get the built-in validation error message for when
    the user's real name is invalid in some way (we wonder how).

    :param name: The proposed user's real name.
    :return: Validation error message.

    """
    return '' if name else accounts.REQUIRED_FIELD_NAME_MSG


def get_username_validation_error(username):
    """Get the built-in validation error message for when
    the username is invalid in some way.

    :param username: The proposed username (unicode).
    :param default: The message to default to in case of no error.
    :return: Validation error message.

    """
    return _validate(_validate_username, errors.AccountUsernameInvalid, username)


def get_email_validation_error(email):
    """Get the built-in validation error message for when
    the email is invalid in some way.

    :param email: The proposed email (unicode).
    :param default: The message to default to in case of no error.
    :return: Validation error message.

    """
    return _validate(_validate_email, errors.AccountEmailInvalid, email)


def get_secondary_email_validation_error(email):
    """
    Get the built-in validation error message for when the email is invalid in some way.

    Arguments:
        email (str): The proposed email (unicode).
    Returns:
        (str): Validation error message.

    """
    return _validate(_validate_secondary_email_doesnt_exist, errors.AccountEmailAlreadyExists, email)


def get_confirm_email_validation_error(confirm_email, email):
    """Get the built-in validation error message for when
    the confirmation email is invalid in some way.

    :param confirm_email: The proposed confirmation email (unicode).
    :param email: The email to match (unicode).
    :param default: THe message to default to in case of no error.
    :return: Validation error message.

    """
    return _validate(_validate_confirm_email, errors.AccountEmailInvalid, confirm_email, email)


def get_password_validation_error(password, username=None, email=None):
    """Get the built-in validation error message for when
    the password is invalid in some way.

    :param password: The proposed password (unicode).
    :param username: The username associated with the user's account (unicode).
    :param email: The email associated with the user's account (unicode).
    :return: Validation error message.

    """
    return _validate(_validate_password, errors.AccountPasswordInvalid, password, username, email)


def get_country_validation_error(country):
    """Get the built-in validation error message for when
    the country is invalid in some way.

    :param country: The proposed country.
    :return: Validation error message.

    """
    return _validate(_validate_country, errors.AccountCountryInvalid, country)


def get_username_existence_validation_error(username):
    """Get the built-in validation error message for when
    the username has an existence conflict.

    :param username: The proposed username (unicode).
    :param default: The message to default to in case of no error.
    :return: Validation error message.

    """
    return _validate(_validate_username_doesnt_exist, errors.AccountUsernameAlreadyExists, username)


def get_email_existence_validation_error(email):
    """Get the built-in validation error message for when
    the email has an existence conflict.

    :param email: The proposed email (unicode).
    :param default: The message to default to in case of no error.
    :return: Validation error message.

    """
    return _validate(_validate_email_doesnt_exist, errors.AccountEmailAlreadyExists, email)


def _get_user_and_profile(username):
    """
    Helper method to return the legacy user and profile objects based on username.
    """
    try:
        existing_user = User.objects.get(username=username)
    except ObjectDoesNotExist:
        raise errors.UserNotFound()

    existing_user_profile, _ = UserProfile.objects.get_or_create(user=existing_user)

    return existing_user, existing_user_profile


def _validate(validation_func, err, *args):
    """Generic validation function that returns default on
    no errors, but the message associated with the err class
    otherwise. Passes all other arguments into the validation function.

    :param validation_func: The function used to perform validation.
    :param err: The error class to catch.
    :param args: The arguments to pass into the validation function.
    :return: Validation error message, or empty string if no error.

    """
    try:
        validation_func(*args)
    except err as validation_err:
        return text_type(validation_err)
    return ''


def _validate_username(username):
    """Validate the username.

    Arguments:
        username (unicode): The proposed username.

    Returns:
        None

    Raises:
        errors.AccountUsernameInvalid

    """
    try:
        _validate_unicode(username)
        _validate_type(username, six.string_types, accounts.USERNAME_BAD_TYPE_MSG)
        _validate_length(
            username,
            accounts.USERNAME_MIN_LENGTH,
            accounts.USERNAME_MAX_LENGTH,
            accounts.USERNAME_BAD_LENGTH_MSG
        )
        with override_language('en'):
            # `validate_username` provides a proper localized message, however the API needs only the English
            # message by convention.
            validate_username(username)
    except (UnicodeError, errors.AccountDataBadType, errors.AccountDataBadLength) as username_err:
        raise errors.AccountUsernameInvalid(text_type(username_err))
    except ValidationError as validation_err:
        raise errors.AccountUsernameInvalid(validation_err.message)


def _validate_email(email):
    """Validate the format of the email address.

    Arguments:
        email (unicode): The proposed email.

    Returns:
        None

    Raises:
        errors.AccountEmailInvalid

    """
    try:
        _validate_unicode(email)
        _validate_type(email, six.string_types, accounts.EMAIL_BAD_TYPE_MSG)
        _validate_length(email, accounts.EMAIL_MIN_LENGTH, accounts.EMAIL_MAX_LENGTH, accounts.EMAIL_BAD_LENGTH_MSG)
        validate_email.message = accounts.EMAIL_INVALID_MSG.format(email=email)
        validate_email(email)
    except (UnicodeError, errors.AccountDataBadType, errors.AccountDataBadLength) as invalid_email_err:
        raise errors.AccountEmailInvalid(text_type(invalid_email_err))
    except ValidationError as validation_err:
        raise errors.AccountEmailInvalid(validation_err.message)


def _validate_confirm_email(confirm_email, email):
    """Validate the confirmation email field.

    :param confirm_email: The proposed confirmation email. (unicode)
    :param email: The email to match. (unicode)
    :return: None

    """
    if not confirm_email or confirm_email != email:
        raise errors.AccountEmailInvalid(accounts.REQUIRED_FIELD_CONFIRM_EMAIL_MSG)


def _validate_password(password, username=None, email=None):
    """Validate the format of the user's password.

    Passwords cannot be the same as the username of the account,
    so we create a temp_user using the username and email to test the password against.
    This user is never saved.

    Arguments:
        password (unicode): The proposed password.
        username (unicode): The username associated with the user's account.
        email (unicode): The email associated with the user's account.

    Returns:
        None

    Raises:
        errors.AccountPasswordInvalid

    """
    try:
        _validate_type(password, six.string_types, accounts.PASSWORD_BAD_TYPE_MSG)
        temp_user = User(username=username, email=email) if username else None
        validate_password(password, user=temp_user)
    except errors.AccountDataBadType as invalid_password_err:
        raise errors.AccountPasswordInvalid(text_type(invalid_password_err))
    except ValidationError as validation_err:
        raise errors.AccountPasswordInvalid(' '.join(validation_err.messages))


def _validate_country(country):
    """Validate the country selection.

    :param country: The proposed country.
    :return: None

    """
    if country == '' or country == '--':
        raise errors.AccountCountryInvalid(accounts.REQUIRED_FIELD_COUNTRY_MSG)


def _validate_username_doesnt_exist(username):
    """Validate that the username is not associated with an existing user.

    :param username: The proposed username (unicode).
    :return: None
    :raises: errors.AccountUsernameAlreadyExists
    """
    if username is not None and username_exists_or_retired(username):
        raise errors.AccountUsernameAlreadyExists(_(accounts.USERNAME_CONFLICT_MSG).format(username=username))


def _validate_email_doesnt_exist(email):
    """Validate that the email is not associated with an existing user.

    :param email: The proposed email (unicode).
    :return: None
    :raises: errors.AccountEmailAlreadyExists
    """
    if email is not None and email_exists_or_retired(email):
        raise errors.AccountEmailAlreadyExists(_(accounts.EMAIL_CONFLICT_MSG).format(email_address=email))


def _validate_secondary_email_doesnt_exist(email):
    """
    Validate that the email is not associated as a secondary email of an existing user.

    Arguments:
        email (unicode): The proposed email.

    Returns:
        None

    Raises:
        errors.AccountEmailAlreadyExists: Raised if given email address is already associated as another
            user's secondary email.
    """
    if email is not None and AccountRecovery.objects.filter(secondary_email=email).exists():
        # pylint: disable=no-member
        raise errors.AccountEmailAlreadyExists(accounts.EMAIL_CONFLICT_MSG.format(email_address=email))


def _validate_password_works_with_username(password, username=None):
    """Run validation checks on whether the password and username
    go well together.

    An example check is to see whether they are the same.

    :param password: The proposed password (unicode).
    :param username: The username associated with the user's account (unicode).
    :return: None
    :raises: errors.AccountPasswordInvalid
    """
    if password == username:
        raise errors.AccountPasswordInvalid(accounts.PASSWORD_CANT_EQUAL_USERNAME_MSG)


def _validate_type(data, type, err):
    """Checks whether the input data is of type. If not,
    throws a generic error message.

    :param data: The data to check.
    :param type: The type to check against.
    :param err: The error message to throw back if data is not of type.
    :return: None
    :raises: errors.AccountDataBadType

    """
    if not isinstance(data, type):
        raise errors.AccountDataBadType(err)


def _validate_length(data, min, max, err):
    """Validate that the data's length is less than or equal to max,
    and greater than or equal to min.

    :param data: The data to do the test on.
    :param min: The minimum allowed length.
    :param max: The maximum allowed length.
    :param err: The error message to throw back if data's length is below min or above max.
    :return: None
    :raises: errors.AccountDataBadLength

    """
    if len(data) < min or len(data) > max:
        raise errors.AccountDataBadLength(err)


def _validate_unicode(data, err=u"Input not valid unicode"):
    """Checks whether the input data is valid unicode or not.

    :param data: The data to check for unicode validity.
    :param err: The error message to throw back if unicode is invalid.
    :return: None
    :raises: UnicodeError

    """
    try:
        if not isinstance(data, str) and not isinstance(data, six.text_type):
            raise UnicodeError(err)
        # In some cases we pass the above, but it's still inappropriate utf-8.
        six.text_type(data)
    except UnicodeError:
        raise UnicodeError(err)

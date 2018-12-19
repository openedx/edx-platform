# -*- coding: utf-8 -*-
"""
Programmatic integration point for User API Accounts sub-application
"""
import datetime
from pytz import UTC

from django.utils.translation import override as override_language, ugettext as _
from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.core.validators import validate_email, ValidationError
from django.http import HttpResponseForbidden
from openedx.core.djangoapps.theming.helpers import get_current_request
from six import text_type

from student.models import (
    AccountRecovery,
    User,
    UserProfile,
    Registration,
    email_exists_or_retired,
    username_exists_or_retired
)
from student import forms as student_forms
from student import views as student_views
from util.model_utils import emit_setting_changed_event
from util.password_policy_validators import validate_password, normalize_password

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api import errors, accounts, forms, helpers
from openedx.core.djangoapps.user_api.config.waffle import (
    PREVENT_AUTH_USER_WRITES,
    SYSTEM_MAINTENANCE_MSG,
    waffle,
)
from openedx.core.djangoapps.user_api.errors import (
    AccountUpdateError,
    AccountValidationError,
    PreferenceValidationError,
)
from openedx.core.djangoapps.user_api.preferences.api import update_user_preferences
from openedx.core.lib.api.view_utils import add_serializer_errors

from .serializers import (
    AccountLegacyProfileSerializer, AccountUserSerializer,
    UserReadOnlySerializer, _visible_fields  # pylint: disable=invalid-name
)

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
    if username is None:
        username = requesting_user.username

    existing_user, existing_user_profile = _get_user_and_profile(username)
    account_recovery = _get_account_recovery(existing_user)

    if requesting_user.username != username:
        raise errors.UserNotAuthorized()

    # If user has requested to change email, we must call the multi-step process to handle this.
    # It is not handled by the serializer (which considers email to be read-only).
    changing_email = False
    if "email" in update:
        changing_email = True
        new_email = update["email"]
        del update["email"]

    # If user has requested to change name, store old name because we must update associated metadata
    # after the save process is complete.
    changing_full_name = False
    old_name = None
    if "name" in update:
        changing_full_name = True
        old_name = existing_user_profile.name

    changing_secondary_email = False
    if "secondary_email" in update:
        changing_secondary_email = True

    # Check for fields that are not editable. Marking them read-only causes them to be ignored, but we wish to 400.
    read_only_fields = set(update.keys()).intersection(
        AccountUserSerializer.get_read_only_fields() + AccountLegacyProfileSerializer.get_read_only_fields()
    )

    # Build up all field errors, whether read-only, validation, or email errors.
    field_errors = {}

    if read_only_fields:
        for read_only_field in read_only_fields:
            field_errors[read_only_field] = {
                "developer_message": u"This field is not editable via this API",
                "user_message": _(u"The '{field_name}' field cannot be edited.").format(field_name=read_only_field)
            }
            del update[read_only_field]

    user_serializer = AccountUserSerializer(existing_user, data=update)
    legacy_profile_serializer = AccountLegacyProfileSerializer(existing_user_profile, data=update)

    for serializer in user_serializer, legacy_profile_serializer:
        field_errors = add_serializer_errors(serializer, update, field_errors)

    # If the user asked to change email, validate it.
    if changing_email:
        try:
            student_views.validate_new_email(existing_user, new_email)
        except ValueError as err:
            field_errors["email"] = {
                "developer_message": u"Error thrown from validate_new_email: '{}'".format(text_type(err)),
                "user_message": text_type(err)
            }

        # Don't process with sending email to given new email, if it is already associated with
        # an account. User must see same success message with no error.
        # This is so that this endpoint cannot be used to determine if an email is valid or not.
        changing_email = new_email and not email_exists_or_retired(new_email)

    if changing_secondary_email:
        try:
            student_views.validate_secondary_email(account_recovery, update["secondary_email"])
        except ValueError as err:
            field_errors["secondary_email"] = {
                "developer_message": u"Error thrown from validate_secondary_email: '{}'".format(text_type(err)),
                "user_message": text_type(err)
            }
        else:
            account_recovery.secondary_email = update["secondary_email"]
            account_recovery.save()

    # If the user asked to change full name, validate it
    if changing_full_name:
        try:
            student_forms.validate_name(update['name'])
        except ValidationError as err:
            field_errors["name"] = {
                "developer_message": u"Error thrown from validate_name: '{}'".format(err.message),
                "user_message": err.message
            }

    # If we have encountered any validation errors, return them to the user.
    if field_errors:
        raise errors.AccountValidationError(field_errors)

    try:
        # If everything validated, go ahead and save the serializers.

        # We have not found a way using signals to get the language proficiency changes (grouped by user).
        # As a workaround, store old and new values here and emit them after save is complete.
        if "language_proficiencies" in update:
            old_language_proficiencies = list(existing_user_profile.language_proficiencies.values('code'))

        for serializer in user_serializer, legacy_profile_serializer:
            serializer.save()

        # if any exception is raised for user preference (i.e. account_privacy), the entire transaction for user account
        # patch is rolled back and the data is not saved
        if 'account_privacy' in update:
            update_user_preferences(
                requesting_user, {'account_privacy': update["account_privacy"]}, existing_user
            )

        if "language_proficiencies" in update:
            new_language_proficiencies = update["language_proficiencies"]
            emit_setting_changed_event(
                user=existing_user,
                db_table=existing_user_profile.language_proficiencies.model._meta.db_table,
                setting_name="language_proficiencies",
                old_value=old_language_proficiencies,
                new_value=new_language_proficiencies,
            )

        # If the name was changed, store information about the change operation. This is outside of the
        # serializer so that we can store who requested the change.
        if old_name:
            meta = existing_user_profile.get_meta()
            if 'old_names' not in meta:
                meta['old_names'] = []
            meta['old_names'].append([
                old_name,
                u"Name change requested through account API by {0}".format(requesting_user.username),
                datetime.datetime.now(UTC).isoformat()
            ])
            existing_user_profile.set_meta(meta)
            existing_user_profile.save()

        # updating extended user profile info
        if 'extended_profile' in update:
            meta = existing_user_profile.get_meta()
            new_extended_profile = update['extended_profile']
            for field in new_extended_profile:
                field_name = field['field_name']
                new_value = field['field_value']
                meta[field_name] = new_value
            existing_user_profile.set_meta(meta)
            existing_user_profile.save()

    except PreferenceValidationError as err:
        raise AccountValidationError(err.preference_errors)
    except (AccountUpdateError, AccountValidationError) as err:
        raise err
    except Exception as err:
        raise AccountUpdateError(
            u"Error thrown when saving account updates: '{}'".format(text_type(err))
        )

    # And try to send the email change request if necessary.
    if changing_email:
        if not settings.FEATURES['ALLOW_EMAIL_ADDRESS_CHANGE']:
            raise AccountUpdateError(u"Email address changes have been disabled by the site operators.")
        try:
            student_views.do_email_change_request(existing_user, new_email)
        except ValueError as err:
            raise AccountUpdateError(
                u"Error thrown from do_email_change_request: '{}'".format(text_type(err)),
                user_message=text_type(err)
            )
    if changing_secondary_email:
        try:
            student_views.do_email_change_request(
                user=existing_user,
                new_email=update["secondary_email"],
                secondary_email_change_request=True,
            )
        except ValueError as err:
            raise AccountUpdateError(
                u"Error thrown from do_email_change_request: '{}'".format(text_type(err)),
                user_message=text_type(err)
            )


@helpers.intercept_errors(errors.UserAPIInternalError, ignore_errors=[errors.UserAPIRequestError])
@transaction.atomic
def create_account(username, password, email):
    """Create a new user account.

    This will implicitly create an empty profile for the user.

    WARNING: This function does NOT yet implement all the features
    in `student/views.py`.  Until it does, please use this method
    ONLY for tests of the account API, not in production code.
    In particular, these are currently missing:

    * 3rd party auth
    * External auth (shibboleth)

    In addition, we assume that some functionality is handled
    at higher layers:

    * Analytics events
    * Activation email
    * Terms of service / honor code checking
    * Recording demographic info (use profile API)
    * Auto-enrollment in courses (if invited via instructor dash)

    Args:
        username (unicode): The username for the new account.
        password (unicode): The user's password.
        email (unicode): The email address associated with the account.

    Returns:
        unicode: an activation key for the account.

    Raises:
        errors.AccountUserAlreadyExists
        errors.AccountUsernameInvalid
        errors.AccountEmailInvalid
        errors.AccountPasswordInvalid
        errors.UserAPIInternalError: the operation failed due to an unexpected error.

    """
    # Check if ALLOW_PUBLIC_ACCOUNT_CREATION flag turned off to restrict user account creation
    if not configuration_helpers.get_value(
            'ALLOW_PUBLIC_ACCOUNT_CREATION',
            settings.FEATURES.get('ALLOW_PUBLIC_ACCOUNT_CREATION', True)
    ):
        return HttpResponseForbidden(_("Account creation not allowed."))

    if waffle().is_enabled(PREVENT_AUTH_USER_WRITES):
        raise errors.UserAPIInternalError(SYSTEM_MAINTENANCE_MSG)

    # Validate the username, password, and email
    # This will raise an exception if any of these are not in a valid format.
    _validate_username(username)
    _validate_password(password, username, email)
    _validate_email(email)

    # Create the user account, setting them to "inactive" until they activate their account.
    user = User(username=username, email=email, is_active=False)
    password = normalize_password(password)
    user.set_password(password)

    try:
        user.save()
    except IntegrityError:
        raise errors.AccountUserAlreadyExists

    # Create a registration to track the activation process
    # This implicitly saves the registration.
    registration = Registration()
    registration.register(user)

    # Create an empty user profile with default values
    UserProfile(user=user).save()

    # Return the activation key, which the caller should send to the user
    return registration.activation_key


def check_account_exists(username=None, email=None):
    """Check whether an account with a particular username or email already exists.

    Keyword Arguments:
        username (unicode)
        email (unicode)

    Returns:
        list of conflicting fields

    Example Usage:
        >>> account_api.check_account_exists(username="bob")
        []
        >>> account_api.check_account_exists(username="ted", email="ted@example.com")
        ["email", "username"]

    """
    conflicts = []

    try:
        _validate_email_doesnt_exist(email)
    except errors.AccountEmailAlreadyExists:
        conflicts.append("email")
    try:
        _validate_username_doesnt_exist(username)
    except errors.AccountUsernameAlreadyExists:
        conflicts.append("username")

    return conflicts


@helpers.intercept_errors(errors.UserAPIInternalError, ignore_errors=[errors.UserAPIRequestError])
def activate_account(activation_key):
    """Activate a user's account.

    Args:
        activation_key (unicode): The activation key the user received via email.

    Returns:
        None

    Raises:
        errors.UserNotAuthorized
        errors.UserAPIInternalError: the operation failed due to an unexpected error.

    """
    if waffle().is_enabled(PREVENT_AUTH_USER_WRITES):
        raise errors.UserAPIInternalError(SYSTEM_MAINTENANCE_MSG)
    try:
        registration = Registration.objects.get(activation_key=activation_key)
    except Registration.DoesNotExist:
        raise errors.UserNotAuthorized
    else:
        # This implicitly saves the registration
        registration.activate()


@helpers.intercept_errors(errors.UserAPIInternalError, ignore_errors=[errors.UserAPIRequestError])
def request_password_change(email, is_secure):
    """Email a single-use link for performing a password reset.

    Users must confirm the password change before we update their information.

    Args:
        email (str): An email address
        orig_host (str): An originating host, extracted from a request with get_host
        is_secure (bool): Whether the request was made with HTTPS

    Returns:
        None

    Raises:
        errors.UserNotFound
        AccountRequestError
        errors.UserAPIInternalError: the operation failed due to an unexpected error.

    """
    # Binding data to a form requires that the data be passed as a dictionary
    # to the Form class constructor.
    form = forms.PasswordResetFormNoActive({'email': email})

    # Validate that a user exists with the given email address.
    if form.is_valid():
        # Generate a single-use link for performing a password reset
        # and email it to the user.
        form.save(
            from_email=configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL),
            use_https=is_secure,
            request=get_current_request(),
        )
    else:
        # No user with the provided email address exists.
        raise errors.UserNotFound


@helpers.intercept_errors(errors.UserAPIInternalError, ignore_errors=[errors.UserAPIRequestError])
def request_account_recovery(email, is_secure):
    """
    Email a single-use link for performing a password reset so users can login with new email and password.

    Arguments:
        email (str): An email address
        is_secure (bool): Whether the request was made with HTTPS

    Raises:
        errors.UserNotFound: Raised if secondary email address does not exist.
    """
    # Binding data to a form requires that the data be passed as a dictionary
    # to the Form class constructor.
    form = student_forms.AccountRecoveryForm({'email': email})

    # Validate that a user exists with the given email address.
    if form.is_valid():
        # Generate a single-use link for performing a password reset
        # and email it to the user.
        form.save(
            from_email=configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL),
            use_https=is_secure,
            request=get_current_request(),
        )
    else:
        # No user with the provided email address exists.
        raise errors.UserNotFound


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


def _get_account_recovery(user):
    """
    helper method to return the account recovery object based on user.
    """
    try:
        account_recovery = user.account_recovery
    except ObjectDoesNotExist:
        account_recovery = AccountRecovery(user=user)

    return account_recovery


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
        _validate_type(username, basestring, accounts.USERNAME_BAD_TYPE_MSG)
        _validate_length(
            username,
            accounts.USERNAME_MIN_LENGTH,
            accounts.USERNAME_MAX_LENGTH,
            accounts.USERNAME_BAD_LENGTH_MSG
        )
        with override_language('en'):
            # `validate_username` provides a proper localized message, however the API needs only the English
            # message by convention.
            student_forms.validate_username(username)
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
        _validate_type(email, basestring, accounts.EMAIL_BAD_TYPE_MSG)
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
        _validate_type(password, basestring, accounts.PASSWORD_BAD_TYPE_MSG)
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
        if not isinstance(data, str) and not isinstance(data, unicode):
            raise UnicodeError(err)
        # In some cases we pass the above, but it's still inappropriate utf-8.
        unicode(data)
    except UnicodeError:
        raise UnicodeError(err)

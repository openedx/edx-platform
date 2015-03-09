from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
import datetime
from pytz import UTC
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from openedx.core.djangoapps.user_api.api.account import (
    AccountUserNotFound, AccountUpdateError, AccountNotAuthorized, AccountValidationError
)
from .serializers import AccountLegacyProfileSerializer, AccountUserSerializer
from student.models import UserProfile
from student.views import validate_new_email, do_email_change_request
from ..models import UserPreference
from . import ACCOUNT_VISIBILITY_PREF_KEY, ALL_USERS_VISIBILITY


def get_account_settings(requesting_user, username=None, configuration=None, view=None):
    """Returns account information for a user serialized as JSON.

    Note:
        If `requesting_user.username` != `username`, this method will return differing amounts of information
        based on who `requesting_user` is and the privacy settings of the user associated with `username`.

    Args:
        requesting_user (User): The user requesting the account information. Only the user with username
            `username` or users with "is_staff" privileges can get full account information.
            Other users will get the account fields that the user has elected to share.
        username (str): Optional username for the desired account information. If not specified,
            `requesting_user.username` is assumed.
        configuration (dict): an optional configuration specifying which fields in the account
            can be shared, and the default visibility settings. If not present, the setting value with
            key ACCOUNT_VISIBILITY_CONFIGURATION is used.
        view (str): An optional string allowing "is_staff" users and users requesting their own
            account information to get just the fields that are shared with everyone. If view is
            "shared", only shared account information will be returned, regardless of `requesting_user`.

    Returns:
         A dict containing account fields.

    Raises:
         AccountUserNotFound: no user with username `username` exists (or `requesting_user.username` if
            `username` is not specified)
    """
    if username is None:
        username = requesting_user.username

    has_full_access = requesting_user.username == username or requesting_user.is_staff
    return_all_fields = has_full_access and view != 'shared'

    existing_user, existing_user_profile = _get_user_and_profile(username)

    user_serializer = AccountUserSerializer(existing_user)
    legacy_profile_serializer = AccountLegacyProfileSerializer(existing_user_profile)

    account_settings = dict(user_serializer.data, **legacy_profile_serializer.data)

    if return_all_fields:
        return account_settings

    if not configuration:
        configuration = settings.ACCOUNT_VISIBILITY_CONFIGURATION

    visible_settings = {}

    profile_privacy = UserPreference.get_preference(existing_user, ACCOUNT_VISIBILITY_PREF_KEY)
    privacy_setting = profile_privacy if profile_privacy else configuration.get('default_visibility')

    if privacy_setting == ALL_USERS_VISIBILITY:
        field_names = configuration.get('shareable_fields')
    else:
        field_names = configuration.get('public_fields')

    for field_name in field_names:
        visible_settings[field_name] = account_settings.get(field_name, None)

    return visible_settings


def update_account_settings(requesting_user, update, username=None):
    """Update user account information.

    Note:
        It is up to the caller of this method to enforce the contract that this method is only called
        with the user who made the request.

    Arguments:
        requesting_user (User): The user requesting to modify account information. Only the user with username
            'username' has permissions to modify account information.
        update (dict): The updated account field values.
        username (string): Optional username specifying which account should be updated. If not specified,
            `requesting_user.username` is assumed.

    Raises:
        AccountUserNotFound: no user with username `username` exists (or `requesting_user.username` if
            `username` is not specified)
        AccountNotAuthorized: the requesting_user does not have access to change the account
            associated with `username`
        AccountValidationError: the update was not attempted because validation errors were found with
            the supplied update
        AccountUpdateError: the update could not be completed. Note that if multiple fields are updated at the same
            time, some parts of the update may have been successful, even if an AccountUpdateError is returned;
            in particular, the user account (not including e-mail address) may have successfully been updated,
            but then the e-mail change request, which is processed last, may throw an error.

    """
    if username is None:
        username = requesting_user.username

    existing_user, existing_user_profile = _get_user_and_profile(username)

    if requesting_user.username != username:
        raise AccountNotAuthorized()

    # If user has requested to change email, we must call the multi-step process to handle this.
    # It is not handled by the serializer (which considers email to be read-only).
    new_email = None
    if "email" in update:
        new_email = update["email"]
        del update["email"]

    # If user has requested to change name, store old name because we must update associated metadata
    # after the save process is complete.
    old_name = None
    if "name" in update:
        old_name = existing_user_profile.name

    # Check for fields that are not editable. Marking them read-only causes them to be ignored, but we wish to 400.
    read_only_fields = set(update.keys()).intersection(
        AccountUserSerializer.Meta.read_only_fields + AccountLegacyProfileSerializer.Meta.read_only_fields
    )

    # Build up all field errors, whether read-only, validation, or email errors.
    field_errors = {}

    if read_only_fields:
        for read_only_field in read_only_fields:
            field_errors[read_only_field] = {
                "developer_message": "This field is not editable via this API",
                "user_message": _("Field '{field_name}' cannot be edited.".format(field_name=read_only_field))
            }
            del update[read_only_field]

    user_serializer = AccountUserSerializer(existing_user, data=update)
    legacy_profile_serializer = AccountLegacyProfileSerializer(existing_user_profile, data=update)

    for serializer in user_serializer, legacy_profile_serializer:
        field_errors = _add_serializer_errors(update, serializer, field_errors)

    # If the user asked to change email, validate it.
    if new_email:
        try:
            validate_new_email(existing_user, new_email)
        except ValueError as err:
            field_errors["email"] = {
                "developer_message": "Error thrown from validate_new_email: '{}'".format(err.message),
                "user_message": err.message
            }

    # If we have encountered any validation errors, return them to the user.
    if field_errors:
        raise AccountValidationError(field_errors)

    try:
        # If everything validated, go ahead and save the serializers.
        for serializer in user_serializer, legacy_profile_serializer:
            serializer.save()

        # If the name was changed, store information about the change operation. This is outside of the
        # serializer so that we can store who requested the change.
        if old_name:
            meta = existing_user_profile.get_meta()
            if 'old_names' not in meta:
                meta['old_names'] = []
            meta['old_names'].append([
                old_name,
                "Name change requested through account API by {0}".format(requesting_user.username),
                datetime.datetime.now(UTC).isoformat()
            ])
            existing_user_profile.set_meta(meta)
            existing_user_profile.save()

    except Exception as err:
        raise AccountUpdateError(
            "Error thrown when saving account updates: '{}'".format(err.message)
        )

    # And try to send the email change request if necessary.
    if new_email:
        try:
            do_email_change_request(existing_user, new_email)
        except ValueError as err:
            raise AccountUpdateError(
                "Error thrown from do_email_change_request: '{}'".format(err.message),
                user_message=err.message
            )


def _get_user_and_profile(username):
    """
    Helper method to return the legacy user and profile objects based on username.
    """
    try:
        existing_user = User.objects.get(username=username)
        existing_user_profile = UserProfile.objects.get(user=existing_user)
    except ObjectDoesNotExist:
        raise AccountUserNotFound()

    return existing_user, existing_user_profile


def _add_serializer_errors(update, serializer, field_errors):
    """
    Helper method that adds any validation errors that are present in the serializer to
    the supplied field_errors dict.
    """
    if not serializer.is_valid():
        errors = serializer.errors
        for key, value in errors.iteritems():
            if isinstance(value, list) and len(value) > 0:
                developer_message = value[0]
            else:
                developer_message = "Invalid value: {field_value}'".format(field_value=update[key])
            field_errors[key] = {
                "developer_message": developer_message,
                "user_message": _("Value '{field_value}' is not valid for field '{field_name}'.".format(
                    field_value=update[key], field_name=key)
                )
            }

    return field_errors

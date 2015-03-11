"""
API for managing user preferences.
"""

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import ugettext as _

from ..api.account import AccountUserNotFound, AccountNotAuthorized
from ..models import UserPreference, PreferenceNotFound, PreferenceValidationError, PreferenceUpdateError
from ..serializers import UserSerializer


def _get_user(requesting_user, username, allow_staff=False):
    """
    Helper method to return the user for a given username.
    """
    try:
        existing_user = User.objects.get(username=username)
    except ObjectDoesNotExist:
        raise AccountUserNotFound()

    if requesting_user.username != username:
        if not requesting_user.is_staff or not allow_staff:
            raise AccountNotAuthorized()

    return existing_user


def get_user_preference(requesting_user, preference_key, username=None):
    """Returns the value of the user preference with the specified key.

    Args:
        requesting_user (User): The user requesting the user preferences. Only the user with username
            `username` or users with "is_staff" privileges can access the preferences.
        preference_key (string): The key for the user preference.
        username (str): Optional username for which to look up the preferences. If not specified,
            `requesting_user.username` is assumed.

    Returns:
         The value for the user preference. If no preference exists with key `preference_key`, returns
         None.

    Raises:
         AccountUserNotFound: no user with username `username` exists (or `requesting_user.username` if
            `username` is not specified)
        AccountNotAuthorized: the requesting_user does not have access to the user preference.
    """
    existing_user = _get_user(requesting_user, username, allow_staff=True)
    return UserPreference.get_preference(existing_user, preference_key)


def get_user_preferences(requesting_user, username=None):
    """Returns all user preferences as a JSON response.

    Args:
        requesting_user (User): The user requesting the user preferences. Only the user with username
            `username` or users with "is_staff" privileges can access the preferences.
        username (str): Optional username for which to look up the preferences. If not specified,
            `requesting_user.username` is assumed.

    Returns:
         A dict containing account fields.

    Raises:
         AccountUserNotFound: no user with username `username` exists (or `requesting_user.username` if
            `username` is not specified)
        AccountNotAuthorized: the requesting_user does not have access to the user preference.
    """
    existing_user = _get_user(requesting_user, username, allow_staff=True)
    user_serializer = UserSerializer(existing_user)
    return user_serializer.data["preferences"]


def update_user_preferences(requesting_user, update, username=None):
    """Update the user preferences for the given username.

    Note:
        It is up to the caller of this method to enforce the contract that this method is only called
        with the user who made the request.

    Arguments:
        requesting_user (User): The user requesting to modify account information. Only the user with username
            'username' has permissions to modify account information.
        update (dict): The updated account field values. Note that null values for a preference will
            be treated as a request to delete the key in question.
        username (string): Optional username specifying which account should be updated. If not specified,
            `requesting_user.username` is assumed.

    Raises:
        AccountUserNotFound: no user with username `username` exists (or `requesting_user.username` if
            `username` is not specified)
        AccountNotAuthorized: the requesting_user does not have access to change the account
            associated with `username`
        PreferenceUpdateError: the update could not be completed.
    """
    existing_user = _get_user(requesting_user, username)
    try:
        # First validate each preference setting
        errors = {}
        for preference_key in update.keys():
            preference_value = update[preference_key]
            try:
                if preference_value is not None:
                    UserPreference.validate_preference(existing_user, preference_key, preference_value)
            except ValidationError as error:
                errors[preference_key] = {
                    "developer_message": error.message
                }
        if errors:
            raise PreferenceValidationError(errors)
        # Then perform the patch
        for preference_key in update.keys():
            preference_value = update[preference_key]
            if preference_value is not None:
                UserPreference.set_preference(existing_user, preference_key, preference_value)
            else:
                UserPreference.delete_preference(existing_user, preference_key)
    except Exception as error:
        raise PreferenceUpdateError(
            "Error thrown when updating preferences: '{}'".format(error.message)
        )


def set_user_preference(requesting_user, preference_key, preference_value, username=None):
    """Update a user preference for the given username.

    Note:
        It is up to the caller of this method to enforce the contract that this method is only called
        with the user who made the request.

    Arguments:
        requesting_user (User): The user requesting to modify account information. Only the user with username
            'username' has permissions to modify account information.
        preference_key (string): The key for the user preference.
        preference_value (string): The value to be stored.
        username (string): Optional username specifying which account should be updated. If not specified,
            `requesting_user.username` is assumed.

    Raises:
        AccountUserNotFound: no user with username `username` exists (or `requesting_user.username` if
            `username` is not specified)
        AccountNotAuthorized: the requesting_user does not have access to change the account
            associated with `username`
        AccountValidationError: the update was not attempted because validation errors were found with
            the supplied update
        PreferenceUpdateError: the update could not be completed.
    """
    existing_user = _get_user(requesting_user, username)
    if preference_value is None or preference_value == '':
        message = _('Preference {preference_key} cannot be set to an empty value').format(
            preference_key=preference_key
        )
        raise PreferenceUpdateError(message, user_message=message)
    try:
        UserPreference.set_preference(existing_user, preference_key, preference_value)
    except PreferenceNotFound:
        raise PreferenceNotFound()
    except Exception as error:
        raise PreferenceUpdateError(
            "Error thrown when setting preference: '{}'".format(error.message)
        )


def delete_user_preference(requesting_user, preference_key, username=None):
    """Deletes a user preference on behalf of a requesting user.

    Note:
        It is up to the caller of this method to enforce the contract that this method is only called
        with the user who made the request.

    Arguments:
        requesting_user (User): The user requesting to delete the preference. Only the user with username
            'username' has permissions to delete their own preference.
        preference_key (string): The key for the user preference.
        username (string): Optional username specifying which account should be updated. If not specified,
            `requesting_user.username` is assumed.

    Raises:
        AccountUserNotFound: no user with username `username` exists (or `requesting_user.username` if
            `username` is not specified)
        AccountNotAuthorized: the requesting_user does not have access to change the account
            associated with `username`
        PreferenceNotFound: the user does not have a preference with the specified key.
        PreferenceUpdateError: the delete could not be completed.
    """
    existing_user = _get_user(requesting_user, username)
    try:
        UserPreference.delete_preference(existing_user, preference_key)
    except PreferenceNotFound:
        raise PreferenceNotFound()
    except Exception as error:
        raise PreferenceUpdateError(
            "Error thrown when deleting preference: '{}'".format(error.message)
        )

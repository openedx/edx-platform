"""
API for managing user preferences.
"""

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from openedx.core.djangoapps.user_api.api.account import AccountUserNotFound, AccountNotAuthorized
from openedx.core.djangoapps.user_api.serializers import UserSerializer


class PreferenceRequestError(Exception):
    """There was a problem with a preference request."""
    pass


class PreferenceNotFound(PreferenceRequestError):
    """The desired user preference was not found."""
    pass


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
         The value for the user preference.

    Raises:
         AccountUserNotFound: no user with username `username` exists (or `requesting_user.username` if
            `username` is not specified)
        AccountNotAuthorized: the requesting_user does not have access to the user preference.
        PreferenceNotFound: the user does not have a preference with the specified key.
    """
    existing_user = _get_user(requesting_user, username, allow_staff=True)
    try:
        preference_value = existing_user.preferences.get(key=preference_key).value
    except ObjectDoesNotExist:
        raise PreferenceNotFound()
    return preference_value


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
        update (dict): The updated account field values.
        username (string): Optional username specifying which account should be updated. If not specified,
            `requesting_user.username` is assumed.

    Raises:
        AccountUserNotFound: no user with username `username` exists (or `requesting_user.username` if
            `username` is not specified)
        AccountNotAuthorized: the requesting_user does not have access to change the account
            associated with `username`
        AccountUpdateError: the update could not be completed. Note that if multiple fields are updated at the same
            time, some parts of the update may have been successful, even if an AccountUpdateError is returned;
            in particular, the user account (not including e-mail address) may have successfully been updated,
            but then the e-mail change request, which is processed last, may throw an error.
    """
    existing_user = _get_user(requesting_user, username)
    for preference_key in update.keys():
        preference_value = update[preference_key]
        if preference_value:
            set_user_preference(requesting_user, preference_key, preference_value, username=username)
        else:
            delete_user_preference(requesting_user, preference_key, username=username)


def set_user_preference(requesting_user, preference_key, value, username=None):
    """Update a user preference for the given username.

    Note:
        It is up to the caller of this method to enforce the contract that this method is only called
        with the user who made the request.

    Arguments:
        requesting_user (User): The user requesting to modify account information. Only the user with username
            'username' has permissions to modify account information.
        preference_key (string): The key for the user preference.
        value (string): The value to be stored.
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
    existing_user = _get_user(requesting_user, username)
    user_preference, __ = existing_user.preferences.get_or_create(user=existing_user, key=preference_key)
    user_preference.value = value
    user_preference.save()


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
        AccountUpdateError: the update could not be completed. Note that if multiple fields are updated at the same
            time, some parts of the update may have been successful, even if an AccountUpdateError is returned;
            in particular, the user account (not including e-mail address) may have successfully been updated,
            but then the e-mail change request, which is processed last, may throw an error.
    """
    existing_user = _get_user(requesting_user, username)
    user_preference = existing_user.preferences.get(key=preference_key)
    user_preference.delete()

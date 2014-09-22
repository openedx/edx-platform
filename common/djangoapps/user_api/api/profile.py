"""Python API for user profiles.

Profile information includes a student's demographic information and preferences,
but does NOT include basic account information such as username/password.

"""
from user_api.models import UserProfile


class ProfileRequestError(Exception):
    """ The request to the API was not valid. """
    pass


# TODO: error subclasses
class ProfileInternalError(Exception):
    """ An error occurred in an API call. """
    pass


FULL_NAME_MAX_LENGTH = 255


def profile_info(username):
    """Retrieve a user's profile information

    Searches either by username or email.

    At least one of the keyword args must be provided.

    Arguments:
        username (unicode): The username of the account to retrieve.

    Returns:
        dict: If profile information was found.
        None: If the provided username did not match any profiles.

    """
    try:
        profile = UserProfile.objects.get(user__username=username)
    except UserProfile.DoesNotExist:
        return None

    profile_dict = {
        'username': profile.user.username,
        'email': profile.user.email,
        'full_name': profile.name,
    }

    return profile_dict


def update_profile(username, full_name=None):
    """Update a user's profile.

    Args:
        username (unicode): The username associated with the account.

    Keyword Arguments:
        full_name (unicode): If provided, set the user's full name to this value.

    Returns:
        None

    Raises:
        ProfileRequestError: If there is no profile matching the provided username.

    """
    try:
        profile = UserProfile.objects.get(user__username=username)
    except UserProfile.DoesNotExist:
        raise ProfileRequestError("TODO")

    if full_name is not None:
        if len(full_name) > FULL_NAME_MAX_LENGTH:
            raise ProfileRequestError("TODO")
        else:
            profile.update_name(full_name)


def preference_info(username, preference_name):
    """Retrieve information about a user's preferences.

    Arguments:
        username (unicode): The username of the account to retrieve.
        preference_name (unicode): The name of the preference to retrieve.

    Returns:
        The JSON-deserialized value.

    """
    pass


def update_preference(username, preference_name, preference_value):
    """Update a user's preference.

    Arguments:
        username (unicode): The username of the account to retrieve.
        preference_name (unicode): The name of the preference to set.
        preference_value (JSON-serializable): The new value for the preference.

    Returns:
        None

    """
    pass

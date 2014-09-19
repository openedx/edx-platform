"""Python API for user profiles.

Profile information includes a student's demographic information and preferences,
but does NOT include basic account information such as username/password.

"""


class ProfileRequestError(Exception):
    """ The request to the API was not valid. """
    pass


class ProfileInternalError(Exception):
    """ An error occurred in an API call. """
    pass


def profile_info(username=None, email=None):
    """Retrieve a user's profile information

    Searches either by username or email.

    At least one of the keyword args must be provided.

    Keyword Arguments:
        username (unicode): The username of the account to retrieve.
        email (unicode): The email associated with the account to retrieve.

    Returns:
        dict or None

    """
    return {}


def update_profile(username, full_name=None):
    """Update a user's profile.

    Args:
        username (unicode): The username associated with the account.

    Keyword Arguments:
        full_name (unicode): If provided, set the user's full name to this value.

    Returns:
        dict

    Raises:
        ProfileRequestError

    """
    pass


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
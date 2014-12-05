"""Python API for user profiles.

Profile information includes a student's demographic information and preferences,
but does NOT include basic account information such as username, password, and
email address.

"""
import datetime
import logging

from django.conf import settings
from django.db import IntegrityError
from pytz import UTC
import analytics

from eventtracking import tracker
from ..models import User, UserProfile, UserPreference, UserOrgTag
from ..helpers import intercept_errors

log = logging.getLogger(__name__)


class ProfileRequestError(Exception):
    """ The request to the API was not valid. """
    pass


class ProfileUserNotFound(ProfileRequestError):
    """ The requested user does not exist. """
    pass


class ProfileInvalidField(ProfileRequestError):
    """ The proposed value for a field is not in a valid format. """

    def __init__(self, field, value):
        super(ProfileInvalidField, self).__init__()
        self.field = field
        self.value = value

    def __str__(self):
        return u"Invalid value '{value}' for profile field '{field}'".format(
            value=self.value,
            field=self.field
        )


class ProfileInternalError(Exception):
    """ An error occurred in an API call. """
    pass


FULL_NAME_MAX_LENGTH = 255
FULL_NAME_MIN_LENGTH = 2


@intercept_errors(ProfileInternalError, ignore_errors=[ProfileRequestError])
def profile_info(username):
    """Retrieve a user's profile information.

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
        "username": profile.user.username,
        "email": profile.user.email,
        "full_name": profile.name,
        "level_of_education": profile.level_of_education,
        "mailing_address": profile.mailing_address,
        "year_of_birth": profile.year_of_birth,
        "goals": profile.goals,
        "city": profile.city,
        "country": unicode(profile.country),
    }

    return profile_dict


@intercept_errors(ProfileInternalError, ignore_errors=[ProfileRequestError])
def update_profile(username, full_name=None):
    """Update a user's profile.

    Arguments:
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
        raise ProfileUserNotFound

    if full_name is not None:
        name_length = len(full_name)
        if name_length > FULL_NAME_MAX_LENGTH or name_length < FULL_NAME_MIN_LENGTH:
            raise ProfileInvalidField("full_name", full_name)
        else:
            profile.update_name(full_name)


@intercept_errors(ProfileInternalError, ignore_errors=[ProfileRequestError])
def preference_info(username):
    """Retrieve information about a user's preferences.

    Arguments:
        username (unicode): The username of the account to retrieve.

    Returns:
        dict: Empty if there is no user

    """
    preferences = UserPreference.objects.filter(user__username=username)

    preferences_dict = {}
    for preference in preferences:
        preferences_dict[preference.key] = preference.value

    return preferences_dict


@intercept_errors(ProfileInternalError, ignore_errors=[ProfileRequestError])
def update_preferences(username, **kwargs):
    """Update a user's preferences.

    Sets the provided preferences for the given user.

    Arguments:
        username (unicode): The username of the account to retrieve.

    Keyword Arguments:
        **kwargs (unicode): Arbitrary key-value preference pairs

    Returns:
        None

    Raises:
        ProfileUserNotFound

    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise ProfileUserNotFound
    else:
        for key, value in kwargs.iteritems():
            UserPreference.set_preference(user, key, value)


@intercept_errors(ProfileInternalError, ignore_errors=[ProfileRequestError])
def update_email_opt_in(username, org, optin):
    """Updates a user's preference for receiving org-wide emails.

    Sets a User Org Tag defining the choice to opt in or opt out of organization-wide
    emails.

    Arguments:
        username (str): The user to set a preference for.
        org (str): The org is used to determine the organization this setting is related to.
        optin (Boolean): True if the user is choosing to receive emails for this organization. If the user is not
            the correct age to receive emails, email-optin is set to False regardless.

    Returns:
        None

    Raises:
        ProfileUserNotFound: Raised when the username specified is not associated with a user.

    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise ProfileUserNotFound

    profile = UserProfile.objects.get(user=user)
    of_age = (
        profile.year_of_birth is None or  # If year of birth is not set, we assume user is of age.
        datetime.datetime.now(UTC).year - profile.year_of_birth >  # pylint: disable=maybe-no-member
        getattr(settings, 'EMAIL_OPTIN_MINIMUM_AGE', 13)
    )

    try:
        preference, _ = UserOrgTag.objects.get_or_create(
            user=user, org=org, key='email-optin'
        )
        preference.value = str(optin and of_age)
        preference.save()

        if settings.FEATURES.get('SEGMENT_IO_LMS') and settings.SEGMENT_IO_LMS_KEY:
            _track_update_email_opt_in(user.id, org, optin)

    except IntegrityError as err:
        log.warn(u"Could not update organization wide preference due to IntegrityError: {}".format(err.message))


def _track_update_email_opt_in(user_id, organization, opt_in):
    """Track an email opt-in preference change.

    Arguments:
        user_id (str): The ID of the user making the preference change.
        organization (str): The organization whose emails are being opted into or out of by the user.
        opt_in (Boolean): Whether the user has chosen to opt-in to emails from the organization.

    Returns:
        None

    """
    event_name = 'edx.bi.user.org_email.opted_in' if opt_in else 'edx.bi.user.org_email.opted_out'
    tracking_context = tracker.get_tracker().resolve_context()

    analytics.track(
        user_id,
        event_name,
        {
            'category': 'communication',
            'label': organization
        },
        context={
            'Google Analytics': {
                'clientId': tracking_context.get('client_id')
            }
        }
    )

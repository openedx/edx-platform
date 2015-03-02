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
from ..accounts.views import AccountView
from ..models import User, UserPreference, UserOrgTag
from ..helpers import intercept_errors

log = logging.getLogger(__name__)


class ProfileRequestError(Exception):
    """ The request to the API was not valid. """
    pass


class ProfileUserNotFound(ProfileRequestError):
    """ The requested user does not exist. """
    pass


class ProfileInternalError(Exception):
    """ An error occurred in an API call. """
    pass


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
        AccountUserNotFound: Raised when the username specified is not associated with a user.

    """
    account_settings = AccountView.get_serialized_account(username)
    year_of_birth = account_settings['year_of_birth']
    of_age = (
        year_of_birth is None or  # If year of birth is not set, we assume user is of age.
        datetime.datetime.now(UTC).year - year_of_birth >  # pylint: disable=maybe-no-member
        getattr(settings, 'EMAIL_OPTIN_MINIMUM_AGE', 13)
    )

    try:
        user = User.objects.get(username=username)
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

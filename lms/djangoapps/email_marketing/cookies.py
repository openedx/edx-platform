"""
This module adds any cookies needed for email marketing
"""
import logging
import datetime

from email_marketing.models import EmailMarketingConfiguration

from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_error import SailthruClientError

log = logging.getLogger(__name__)


def add_email_marketing_cookies(response, user):
    """
    Directly called (non-signal) function for adding any cookies needed for email marketing

    Args:
        response: http response object
        user: The user object for the user being changed

    Returns:
        response: http response object with cookie added
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return response

    try:
        sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
        sailthru_response = sailthru_client.api_post("user", {'id': user.email,
                                                              'fields': {'keys': 1},
                                                              'vars': datetime.datetime.now().strftime("%Y-%m-%d")})
    except SailthruClientError as exc:
        log.error("Exception attempting to obtain cookie from Sailthru: %s", unicode(exc))
        return response

    if sailthru_response.is_ok():
        if 'keys' in sailthru_response.json and 'cookie' in sailthru_response.json['keys']:
            cookie = sailthru_response.json['keys']['cookie']

            response.set_cookie(
                'sailthru_hid',
                cookie,
                max_age=365 * 24 * 60 * 60  # set for 1 year
            )
        else:
            log.error("No cookie returned attempting to obtain cookie from Sailthru for %s", user.email)
    else:
        error = sailthru_response.get_error()
        log.error("Error attempting to obtain cookie from Sailthru: %s", error.get_message())
    return response

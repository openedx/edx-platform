"""
Wrapper to use pwnedpassword Service
"""


import logging

import requests
from requests.exceptions import ReadTimeout
from rest_framework.status import HTTP_408_REQUEST_TIMEOUT

from openedx.core.djangoapps.user_authn.config.waffle import ENABLE_PWNED_PASSWORD_API

log = logging.getLogger(__name__)


def convert_password_tuple(value):
    """
    a conversion function used to convert a string to a tuple
    """
    signature, count = value.split(":")
    return (signature, int(count))


class PwnedPasswordsAPI:
    """
    WrapperClass on pwned password service
    to fetch similar password signatures
    along with their count
    """
    API_URL = "https://api.pwnedpasswords.com"

    @staticmethod
    def range(password):
        """
        Returns a dict containing hashed password signatures along with their count

        **Argument(s):
            password: a sha-1-hashed string against which pwnedservice is invoked

        **Returns:
            {
                "7ecd77ecd7": 341,
                "7ecd77ecd77ecd7": 12,
            }
        """
        range_url = PwnedPasswordsAPI.API_URL + '/range/{}'.format(password[:5])

        if ENABLE_PWNED_PASSWORD_API.is_enabled():
            try:
                response = requests.get(range_url, timeout=5)
                entries = dict(map(convert_password_tuple, response.text.split("\r\n")))
                return entries

            except ReadTimeout:
                log.warning('Request timed out for {}'.format(password))
                return HTTP_408_REQUEST_TIMEOUT

            except Exception as exc:  # pylint: disable=W0703
                log.exception(f"Unable to range the password: {exc}")

"""
A utility class which provides implementation to create new users on Braze.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class BrazeCreateUser:
    """
        A class to create users on Braze. This makes use of the Braze REST API to create new user.

        See the Braze documentation for message sending, for more information:
        https://www.braze.com/docs/api/endpoints/user_data/post_user_alias/

        Example:

            Sample settings::

                .. settings_start
                ACE_CHANNEL_BRAZE_CREATE_USER_API_KEY = "1c304d0d-c800-4da3-bfaa-41b1189b34cb"
                ACE_CHANNEL_BRAZE_REST_ENDPOINT = "rest.iad-01.braze.com"
                .. settings_end
        """

    _API_KEY_SETTING = 'ACE_CHANNEL_BRAZE_CREATE_USER_API_KEY'
    _ENDPOINT_SETTING = 'ACE_CHANNEL_BRAZE_REST_ENDPOINT'

    @classmethod
    def enabled(cls):
        """
        Returns: True iff all required settings are not empty and the Braze client library is installed.
        """
        ok = True

        for setting in (
            cls._API_KEY_SETTING,
            cls._ENDPOINT_SETTING,
        ):
            if not getattr(settings, setting, None):
                ok = False
                logger.warning('%s is not set, Braze email channel is disabled.', setting)

        return ok

    @classmethod
    def _auth_headers(cls):
        """Returns authorization headers suitable for passing to the requests library"""
        return {
            'Authorization': 'Bearer ' + getattr(settings, cls._API_KEY_SETTING),
        }

    @classmethod
    def _send_url(cls):
        """Returns the send-message API URL"""
        return 'https://{url}/users/alias/new'.format(url=getattr(settings, cls._ENDPOINT_SETTING))

    @classmethod
    def create_user(cls, user):
        if not cls.enabled():
            return

        response = requests.post(
            cls._send_url(),
            headers=cls._auth_headers(),
            json={
                "user_aliases" :
                [
                    {
                        "external_id": user.id,
                        "alias_name" : "first_name",
                        "alias_label" : user.profile.name
                    },
                    {
                        "external_id": user.id,
                        "alias_name": "email",
                        "alias_label": user.email
                    }
                ]
            }
        )

        try:
            response.raise_for_status()
            logger.debug('Successfully sent to Braze')

        except requests.exceptions.HTTPError as exc:
            # https://www.braze.com/docs/api/errors/
            message = response.json().get('message', 'Unknown error')
            logger.info('Failed to send to Braze: %s', message)

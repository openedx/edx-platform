"""
Client for Sending Emails with HubSpot.
"""
import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class HubSpotClient:
    """
    HubSpot Client
    """

    ACCOUNT_ACTIVATION_EMAIL = '74553115138'
    PASSWORD_RESET_EMAIL = '74589854319'
    PASSWORD_RESET_COMPLETE = '74591235508'
    COURSE_COMPLETION = '74600305296'
    SELF_PACED_COURSE_ENROLLMENT_EMAIL = '74616750411'
    CERTIFICATE_READY_TO_DOWNLOAD = '74613102189'
    ORG_ADMIN_ACTIVATION = '75041803894'
    ORG_ADMIN_CHANGE = '75041806097'
    ORG_ADMIN_GET_IN_TOUCH = '75043535449'
    ORG_NEW_ADMIN_GET_IN_TOUCH = '75043537509'

    def __init__(self):
        """
        Initialize HubSpot Client.
        """
        self.api_key = settings.HUBSPOT_API_KEY
        self.HUBSPOT_API_URL = 'https://api.hubapi.com'

    def send_mail(self, email_data):
        """
        Sends POST request to HubSpot API to send an email.

        Arguments:
            email_data (dict): Contains hubspot post data.
        """
        logger.info('Sending Email With HubSpot, Email Data: {email_data}'.format(email_data=email_data))

        url = '{hubspot_api_url}/marketing/v3/transactional/single-email/send?hapikey={api_key}'.format(
            hubspot_api_url=self.HUBSPOT_API_URL,
            api_key=self.api_key
        )
        headers = {'Content-type': 'application/json'}
        response = requests.post(url, headers=headers, json=email_data)

        logger.info(response.json())
        return response

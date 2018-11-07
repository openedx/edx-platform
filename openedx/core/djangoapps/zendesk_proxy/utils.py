"""
Utility functions for zendesk interaction.
"""
import json
import logging
from urlparse import urljoin

from django.conf import settings
import requests
from rest_framework import status

log = logging.getLogger(__name__)


def create_zendesk_ticket(requester_name, requester_email, subject, body, custom_fields=None, uploads=None, tags=None):
    """
    Create a Zendesk ticket via API.

    Note that we do this differently in other locations (lms/djangoapps/commerce/signals.py and
    common/djangoapps/util/views.py). Both of those callers use basic auth, and should be switched over to this oauth
    implementation once the immediate pressures of zendesk_proxy are resolved.
    """
    def _std_error_message(details, payload):
        """Internal helper to standardize error message. This allows for simpler splunk alerts."""
        return 'zendesk_proxy action required\n{}\nNo ticket created for payload {}'.format(details, payload)

    if tags:
        # Remove duplicates from tags list
        tags = list(set(tags))

    data = {
        'ticket': {
            'requester': {
                'name': requester_name,
                'email': requester_email
            },
            'subject': subject,
            'comment': {
                'body': body,
                'uploads': uploads
            },
            'custom_fields': custom_fields,
            'tags': tags
        }
    }

    # Encode the data to create a JSON payload
    payload = json.dumps(data)

    if not (settings.ZENDESK_URL and settings.ZENDESK_OAUTH_ACCESS_TOKEN):
        log.error(_std_error_message("zendesk not configured", payload))
        return status.HTTP_503_SERVICE_UNAVAILABLE

    # Set the request parameters
    url = urljoin(settings.ZENDESK_URL, '/api/v2/tickets.json')
    headers = {
        'content-type': 'application/json',
        'Authorization': "Bearer {}".format(settings.ZENDESK_OAUTH_ACCESS_TOKEN),
    }

    try:
        response = requests.post(url, data=payload, headers=headers)

        # Check for HTTP codes other than 201 (Created)
        if response.status_code == status.HTTP_201_CREATED:
            log.debug('Successfully created ticket for {}'.format(requester_email))
        else:
            log.error(
                _std_error_message(
                    'Unexpected response: {} - {}'.format(response.status_code, response.content),
                    payload
                )
            )
        return response.status_code
    except Exception:  # pylint: disable=broad-except
        log.exception(_std_error_message('Internal server error', payload))
        return status.HTTP_500_INTERNAL_SERVER_ERROR

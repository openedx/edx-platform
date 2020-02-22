"""
Utility functions for zendesk interaction.
"""


import json
import logging

import requests
from django.conf import settings
from rest_framework import status
from six.moves.urllib.parse import urljoin  # pylint: disable=import-error

log = logging.getLogger(__name__)


def _std_error_message(details, payload):
    """Internal helper to standardize error message. This allows for simpler splunk alerts."""
    return u'zendesk_proxy action required\n{}\nNo ticket created for payload {}'.format(details, payload)


def _get_request_headers():
    return {
        'content-type': 'application/json',
        'Authorization': u"Bearer {}".format(settings.ZENDESK_OAUTH_ACCESS_TOKEN),
    }


def create_zendesk_ticket(
        requester_name,
        requester_email,
        subject,
        body,
        group=None,
        custom_fields=None,
        uploads=None,
        tags=None,
        additional_info=None
):
    """
    Create a Zendesk ticket via API.
    """
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

    if group:
        if group in settings.ZENDESK_GROUP_ID_MAPPING:
            group_id = settings.ZENDESK_GROUP_ID_MAPPING[group]
            data['ticket']['group_id'] = group_id
        else:
            msg = u"Group ID not found for group {}. Please update ZENDESK_GROUP_ID_MAPPING".format(group)
            log.error(_std_error_message(msg, payload))
            return status.HTTP_400_BAD_REQUEST

    # Set the request parameters
    url = urljoin(settings.ZENDESK_URL, '/api/v2/tickets.json')

    try:
        response = requests.post(url, data=payload, headers=_get_request_headers())

        # Check for HTTP codes other than 201 (Created)
        if response.status_code == status.HTTP_201_CREATED:
            log.debug(u'Successfully created ticket for {}'.format(requester_email))
        else:
            log.error(
                _std_error_message(
                    u'Unexpected response: {} - {}'.format(response.status_code, response.content),
                    payload
                )
            )
        if additional_info:
            try:
                ticket = response.json()['ticket']
            except (ValueError, KeyError):
                log.error(
                    _std_error_message(
                        u"Got an unexpected response from zendesk api. Can't"
                        u" get the ticket number to add extra info. {}".format(additional_info),
                        response.content
                    )
                )
                return status.HTTP_400_BAD_REQUEST
            return post_additional_info_as_comment(ticket['id'], additional_info)

        return response.status_code
    except Exception:  # pylint: disable=broad-except
        log.exception(_std_error_message('Internal server error', payload))
        return status.HTTP_500_INTERNAL_SERVER_ERROR


def post_additional_info_as_comment(ticket_id, additional_info):
    """
    Post the Additional Provided as a comment, So that it is only visible
    to management and not students.
    """
    additional_info_string = (
        u"Additional information:\n\n" +
        u"\n".join(u"%s: %s" % (key, value) for (key, value) in additional_info.items() if value is not None)
    )

    data = {
        'ticket': {
            'comment': {
                'body': additional_info_string,
                'public': False
            }
        }
    }

    url = urljoin(settings.ZENDESK_URL, 'api/v2/tickets/{}.json'.format(ticket_id))

    try:
        response = requests.put(url, data=json.dumps(data), headers=_get_request_headers())
        if response.status_code == 200:
            log.debug(u'Successfully created comment for ticket {}'.format(ticket_id))
        else:
            log.error(
                _std_error_message(
                    u'Unexpected response: {} - {}'.format(response.status_code, response.content),
                    data
                )
            )
        return response.status_code
    except Exception:  # pylint: disable=broad-except
        log.exception(_std_error_message('Internal server error', data))
        return status.HTTP_500_INTERNAL_SERVER_ERROR

"""
Utility functions for zendesk interaction.
"""

from __future__ import absolute_import
import json
import logging
from six.moves.urllib.parse import urljoin  # pylint: disable=import-error

from django.conf import settings
import requests
from rest_framework import status


log = logging.getLogger(__name__)


def _std_error_message(details, payload):
    """Internal helper to standardize error message. This allows for simpler splunk alerts."""
    return u'zendesk_proxy action required\n{}\nNo ticket created for payload {}'.format(details, payload)


def _get_request_headers():
    return {
        'content-type': 'application/json',
        'Authorization': u"Bearer {}".format(settings.ZENDESK_OAUTH_ACCESS_TOKEN),
    }

def create_zendesk_ticket(requester_name, requester_email, subject, body, group=None, custom_fields=None, uploads=None, tags=None, additional_info=None):
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

    if not (settings.ZENDESK_URL and settings.ZENDESK_OAUTH_ACCESS_TOKEN):
        log.error(_std_error_message("zendesk not configured", data))
        return status.HTTP_503_SERVICE_UNAVAILABLE

    if group:
        group_id = get_zendesk_group_by_name(group)
        data['ticket']['group_id'] = group_id

    # Encode the data to create a JSON payload
    payload = json.dumps(data)

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
            ticket = json.loads(response.text)['ticket']
            return post_additional_info_as_comment(ticket['id'], additional_info)

        return response.status_code
    except Exception:  # pylint: disable=broad-except
        log.exception(_std_error_message('Internal server error', payload))
        return status.HTTP_500_INTERNAL_SERVER_ERROR


def get_zendesk_group_by_name(name):
    """
    Calls the Zendesk list-groups api

    Returns the group Id matching the name.
    """
    url = urljoin(settings.ZENDESK_URL, '/api/v2/groups.json')

    try:
        response = requests.post(url, headers=_get_request_headers())

        groups = json.loads(response.text)['groups']
        for group in groups:
            if group['name'] == name:
                return group['id']
    except Exception as e:  # pylint: disable=broad-except
        log.exception(_std_error_message('Internal server error', 'None'))
    
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    log.exception(_std_error_message('Tried to get zendesk group which does not exist', name))
    raise Exception


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
                'publuc': False
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

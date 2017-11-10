"""
NotificationChannelProvider to integrate with the Urban Airship mobile push
notification services
"""
import json
import logging

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from edx_notifications.channels.channel import BaseNotificationChannelProvider

# system defined constants that only we should know about
UA_API_PUSH_ENDPOINT = 'https://go.urbanairship.com/api/push/'
PUSH_REQUEST_HEADER = {
    'Content-Type': 'application/json',
    'Accept': 'application/vnd.urbanairship+json; version=3;'
}

log = logging.getLogger(__name__)


class UrbanAirshipNotificationChannelProvider(BaseNotificationChannelProvider):
    """
    Implementation of the BaseNotificationChannelProvider abstract interface
    """

    def __init__(self, name=None, display_name=None, display_description=None, link_resolvers=None):
        """
        Initializer
        """
        super(UrbanAirshipNotificationChannelProvider, self).__init__(
            name=name,
            display_name=display_name,
            display_description=display_description,
            link_resolvers=link_resolvers
        )

    def dispatch_notification_to_user(self, user_id, msg, channel_context=None):
        """
        Send a notification to a user. It is assumed that
        'user_id' and 'msg' are valid and have already passed
        all necessary validations
        :param user_id:
        :param msg:
        :param channel_context:
        :return:
        """
        payload = self.create_payload(msg, user_id)
        payload = json.dumps(payload)
        api_credentials = channel_context.get('api_credentials') if channel_context else None
        return self.call_ua_push_api(payload, api_credentials)

    @staticmethod
    def create_payload(msg, user_id):
        """
        Creates payload for UA push request for single named user
        :param msg:
        :param user_id:
        :return:
        """
        assert msg.payload['title'], 'Notification title not available in payload'
        assert user_id, 'No user id given'
        obj = {
            "notification": {"alert": msg.payload['title']},
            "audience": {"named_user": str(user_id)},
            "device_types": ["ios", "android"]
        }

        return obj

    def call_ua_push_api(self, payload, api_credentials):
        """
        Calls Urban Airship push API to send push notifications
        :param payload: json payload to be passed to push notifications API
        :param api_credentials: dict containing provider id and secret key
        Returns: json response sent by UA
        """
        resp = {}
        try:
            resp = requests.post(
                UA_API_PUSH_ENDPOINT,
                payload,
                headers=PUSH_REQUEST_HEADER,
                auth=HTTPBasicAuth(api_credentials["provider_key"], api_credentials["provider_secret"])
            )
            resp = resp.json()
            if not resp['ok']:
                log.error(
                    "Urban Airship push notifications API failed. Details: %s Error: %s",
                    resp.get('details'), resp.get('error')
                )

        except RequestException as ex:
            log.error("Urban Airship push notifications API failed with error %s", ex.message)
        return resp

    def bulk_dispatch_notification(self, user_ids, msg, exclude_user_ids=None, channel_context=None):
        """
        Perform a bulk dispatch of the notification message to
        all user_ids that will be enumerated over in user_ids.
        :param user_ids:
        :param msg:
        :param exclude_user_ids:
        :param channel_context:
        :return:
        """
        if 'tag_group' in msg.payload:
            payload = self.create_tag_group_payload(msg)
        elif 'send_to_all' in msg.payload and msg.payload['send_to_all'] is True:
            payload = self.create_all_user_payload(msg)
        else:
            exclude_user_ids = exclude_user_ids if exclude_user_ids else []
            actual_user_ids = []
            for user_id in user_ids:
                if user_id not in exclude_user_ids:
                    actual_user_ids.append(user_id)
            payload = self.create_bulk_user_payload(actual_user_ids, msg)
        payload = json.dumps(payload)
        api_credentials = channel_context.get('api_credentials') if channel_context else None
        return self.call_ua_push_api(payload, api_credentials)

    @staticmethod
    def create_tag_group_payload(msg):
        """
        Creates payload for UA push request for tag group
        :param msg:
        :return:
        """
        assert msg.payload['title'], 'Notification title not available in payload'
        alert = msg.payload['title']
        group = msg.payload.get('tag_group', 'enrollments')
        tag = msg.payload.get('tag', msg.namespace)

        obj = {
            "notification": {
                "alert": alert,
            },
            "device_types": "all",
            "audience": {
                "group": group,
                "tag": tag
            }
        }
        if 'open_url' in msg.payload:
            obj["notification"]["actions"] = {
                "open": {
                    "type": "url",
                    "content": msg.payload['open_url']
                }
            }

        return obj

    @staticmethod
    def create_bulk_user_payload(user_ids, msg):
        """
        Creates payload to send UA push notification to list of users
        :param user_ids: list of user ids
        :param msg:
        :return:
        """
        assert user_ids, 'List of user ids is empty'
        assert msg.payload['title'], 'Notification title not available in payload'

        obj = {
            "notification": {
                "alert": msg.payload['title']
            },
            "device_types": ["ios", "android"],
            "audience": {
                "named_user": [str(user_id) for user_id in user_ids]
            }
        }

        return obj

    @staticmethod
    def create_all_user_payload(msg):
        """
        Creates payload to send UA push notification to all users
        :param msg:
        :return:
        """
        assert msg.payload['title'], 'Notification title not available in payload'

        obj = {
            "notification": {
                "alert": msg.payload['title']
            },
            "device_types": "all",
            "audience": "all"
        }

        return obj

    def resolve_msg_link(self, msg, link_name, params, channel_context=None):
        """
        Generates the appropriate link given a msg, a link_name, and params
        """
        # Click through links do not apply for mobile push notifications
        return None

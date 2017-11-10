"""
Test cases for the serializers
"""

import pytz
import json
from dateutil import parser
from django.test import TestCase

from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from datetime import datetime

from edx_notifications.data import (  # pylint: disable=unused-import
    NotificationMessage,
    NotificationType,
)
from edx_notifications.serializers import (
    NotificationMessageSerializer
)


class SerializerTests(TestCase):
    """
    Go through all the test cases of the serializers.py
    """

    def test_message_serialization(self):
        """
        Test serialization/deserialization of a sample Notification Message
        """

        msg = NotificationMessage(
            id=1001,
            msg_type=NotificationType(
                name='edx_notifications.sample',
                renderer='foo.renderer',
            ),
            namespace='my-namespace',
            payload={
                'name1': 'val1',
                'name2': datetime.utcnow(),
            },
            deliver_no_earlier_than=datetime.utcnow(),
            created=datetime.utcnow(),
        )

        serializer = NotificationMessageSerializer(msg)
        json_data = JSONRenderer().render(serializer.data)

        # no deserialize the string and compare resulting objects
        stream = BytesIO(json_data)
        data = JSONParser().parse(stream)

        deserializer = NotificationMessageSerializer(data=data)
        self.assertTrue(deserializer.is_valid())

        # compare the original data object to our deserialized version
        # and make sure they are the same
        msg_payload = json.loads(deserializer.data['payload'])
        msg_output = NotificationMessage(
            id=deserializer.data['id'],
            msg_type=NotificationType(
                name=deserializer.data['msg_type']['name'],
                renderer=deserializer.data['msg_type']['renderer'],
            ),
            namespace=deserializer.data['namespace'],
            payload={
                'name1': msg_payload['name1'],
                'name2': msg_payload['name2'],
            },
            deliver_no_earlier_than=parser.parse(
                deserializer.data['deliver_no_earlier_than']
            ).replace(tzinfo=pytz.timezone('UTC')),
            created=parser.parse(deserializer.data['created']).replace(tzinfo=pytz.timezone('UTC')),
        )
        self.assertEqual(msg.namespace, msg_output.namespace)
        self.assertEqual(msg.msg_type, msg_output.msg_type)  # pylint: disable=maybe-no-member

        # now intentionally try to break it
        data['namespace'] = 'busted'
        data['msg_type']['name'] = 'not-same'

        deserializer = NotificationMessageSerializer(data=data)
        self.assertTrue(deserializer.is_valid())

        # compare the original data object to our deserialized version
        # and make sure they are not considered the same
        msg_payload = json.loads(deserializer.data['payload'])
        msg_output = NotificationMessage(
            id=deserializer.data['id'],
            msg_type=NotificationType(
                name=deserializer.data['msg_type']['name'],
                renderer=deserializer.data['msg_type']['renderer'],
            ),
            namespace=deserializer.data['namespace'],
            payload={
                'name1': msg_payload['name1'],
                'name2': msg_payload['name2'],
            },
            deliver_no_earlier_than=parser.parse(
                deserializer.data['deliver_no_earlier_than']
            ).replace(tzinfo=pytz.timezone('UTC')),
            created=parser.parse(deserializer.data['created']).replace(tzinfo=pytz.timezone('UTC')),
        )
        self.assertNotEqual(msg.namespace, msg_output.namespace)
        self.assertNotEqual(msg.msg_type, msg_output.msg_type)  # pylint: disable=maybe-no-member

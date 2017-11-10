"""
Unit tests to exercise code implemented in data.py
"""

from django.test import TestCase

from django.core.exceptions import ValidationError

from edx_notifications.data import (
    NotificationMessage,
)


class DataTests(TestCase):
    """
    Go through data.py and exercise some tests
    """

    def test_message_validation(self):
        """
        Make sure validation of NotificationMessage is correct
        """

        msg = NotificationMessage()  # intentionally blank

        with self.assertRaises(ValidationError):
            msg.validate()

    def test_cloning(self):
        """
        Make sure cloning works
        """

        msg = NotificationMessage(
            payload={'foo': 'bar'}
        )

        clone = NotificationMessage.clone(msg)

        self.assertEqual(msg, clone)

        # now change the cloned payload and assert that the original one
        # did not change

        clone.payload['foo'] = 'changed'
        self.assertEqual(msg.payload['foo'], 'bar')
        self.assertEqual(clone.payload['foo'], 'changed')

    def test_click_links_params(self):
        """
        Make sure the helper methods work
        """

        msg = NotificationMessage(
            payload={'foo': 'bar'}
        )

        msg.add_click_link_params({
            'param1': 'val1',
            'param2': 'val2',
        })

        click_links = msg.get_click_link_params()

        self.assertIsNotNone(click_links)
        self.assertEqual(click_links['param1'], 'val1')
        self.assertEqual(click_links['param2'], 'val2')

        msg.add_click_link_params({
            'param3': 'val3',
        })

        click_links = msg.get_click_link_params()

        self.assertEqual(click_links['param1'], 'val1')
        self.assertEqual(click_links['param2'], 'val2')
        self.assertEqual(click_links['param3'], 'val3')

    def test_click_link(self):
        """
        Tests around the click_link property of NotificationMessages
        """

        msg = NotificationMessage()

        self.assertIsNone(msg.get_click_link())

        msg.set_click_link('/foo/bar/baz')
        self.assertEqual(msg.get_click_link(), '/foo/bar/baz')

        msg.set_click_link('/updated')
        self.assertEqual(msg.get_click_link(), '/updated')

    def test_multi_payloads(self):
        """
        Tests the ability to support multiple payloads in a NotificationMessage
        """

        msg = NotificationMessage()
        self.assertIsNone(msg.get_payload())

        msg.add_payload(
            {
                'foo': 'bar',
            }
        )

        self.assertEqual(msg.get_payload(), {'foo': 'bar'})
        self.assertEqual(msg.get_message_for_channel(), msg)

        msg.add_payload(
            {
                'bar': 'baz'
            },
            channel_name='channel1'
        )

        self.assertNotEqual(msg.get_message_for_channel(), msg)
        self.assertEqual(msg.get_message_for_channel().payload, {'foo': 'bar'})
        self.assertEqual(msg.get_message_for_channel('channel1').payload, {'bar': 'baz'})

        msg.add_payload(
            {
                'one': 'two'
            },
            channel_name='channel2'
        )

        self.assertNotEqual(msg.get_message_for_channel(), msg)
        self.assertEqual(msg.get_message_for_channel().payload, {'foo': 'bar'})
        self.assertEqual(msg.get_message_for_channel('channel1').payload, {'bar': 'baz'})
        self.assertEqual(msg.get_message_for_channel('channel2').payload, {'one': 'two'})
        self.assertEqual(msg.get_message_for_channel('doesnt-exist').payload, {'foo': 'bar'})

        msg.add_payload(
            {
                'updated': 'yes'
            }
        )
        self.assertEqual(msg.get_message_for_channel().payload, {'updated': 'yes'})

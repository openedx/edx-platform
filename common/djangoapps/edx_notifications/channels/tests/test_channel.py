"""
All tests regarding channel.py
"""

from django.test import TestCase
from django.test.utils import override_settings
from django.core.exceptions import ImproperlyConfigured

from edx_notifications.channels.channel import (
    get_notification_channel,
    reset_notification_channels,
    BaseNotificationChannelProvider,
)

from edx_notifications.channels.null import NullNotificationChannel

from edx_notifications.channels.durable import BaseDurableNotificationChannel

from edx_notifications.data import (
    NotificationType,
)

# list all known channel providers
_NOTIFICATION_CHANNEL_PROVIDERS = {
    'default': {
        'class': 'edx_notifications.channels.durable.BaseDurableNotificationChannel',
        'options': {
            'display_name': 'channel_default',
            'display_description': 'channel_description_default',
        }
    },
    'channel1': {
        'class': 'edx_notifications.channels.durable.BaseDurableNotificationChannel',
        'options': {
            'display_name': 'channel_name1',
            'display_description': 'channel_description1',
        }
    },
    'channel2': {
        'class': 'edx_notifications.channels.durable.BaseDurableNotificationChannel',
        'options': {
            'display_name': 'channel_name2',
            'display_description': 'channel_description2',
        }
    },
    'channel3': {
        'class': 'edx_notifications.channels.durable.BaseDurableNotificationChannel',
        'options': {
            'display_name': 'channel_name3',
            'display_description': 'channel_description3',
        }
    },
    'channel4': {
        'class': 'edx_notifications.channels.durable.BaseDurableNotificationChannel',
        'options': {
            'display_name': 'channel_name4',
            'display_description': 'channel_description4',
        }
    },
    'channel5': {
        'class': 'edx_notifications.channels.durable.BaseDurableNotificationChannel',
        'options': {
            'display_name': 'channel_name5',
            'display_description': 'channel_description5',
        }
    },
    'channel6': {
        'class': 'edx_notifications.channels.durable.BaseDurableNotificationChannel',
        'options': {
            'display_name': 'channel_name6',
            'display_description': 'channel_description6',
        }
    },
    'null': {
        'class': 'edx_notifications.channels.null.NullNotificationChannel',
        'options': {}
    },
}

# list all of the mappings of notification types to channel
_NOTIFICATION_CHANNEL_PROVIDER_TYPE_MAPS = {
    '*': 'default',  # default global mapping
    'edx_notifications.*': 'channel1',
    'edx_notifications.channels.*': 'channel2',
    'edx_notifications.channels.tests.*': 'channel3',
    'edx_notifications.channels.tests.test_channel.*': 'channel4',
    'edx_notifications.channels.tests.test_channel.channeltests.*': 'channel5',
    'edx_notifications.channels.tests.test_channel.channeltests.foo': 'channel6',
    'edx_notifications.channels.tests.test_channel.channeltests.null': 'null',
}


class BadChannel(BaseNotificationChannelProvider):
    """
    A poorly formed Channel for testing purposes
    """

    def dispatch_notification_to_user(self, user_id, msg, channel_context=None):
        """
        This will raise an error
        """
        raise super(BadChannel, self).dispatch_notification_to_user(
            user_id,
            msg,
            channel_context=channel_context
        )

    def bulk_dispatch_notification(self, user_ids, msg, exclude_user_ids=None, channel_context=None):
        """
        Perform a bulk dispatch of the notification message to
        all user_ids that will be enumerated over in user_ids.
        """
        raise super(BadChannel, self).bulk_dispatch_notification(
            user_ids,
            msg,
            channel_context=channel_context
        )

    def resolve_msg_link(self, msg, link_name, params, channel_context=None):
        """
        Generates the appropriate link given a msg, a link_name, and params
        """
        raise super(BadChannel, self).resolve_msg_link(
            msg,
            link_name,
            params,
            channel_context=channel_context
        )


@override_settings(NOTIFICATION_CHANNEL_PROVIDERS=_NOTIFICATION_CHANNEL_PROVIDERS)
@override_settings(NOTIFICATION_CHANNEL_PROVIDER_TYPE_MAPS=_NOTIFICATION_CHANNEL_PROVIDER_TYPE_MAPS)
class ChannelTests(TestCase):
    """
    Tests for channel.py
    """

    def setUp(self):
        """
        Harnessing
        """
        reset_notification_channels()
        self.test_user_id = 1001  # an arbitrary user_id
        self.test_msg_type = NotificationType(
            name='edx_notifications.channels.tests.test_channel.channeltests.foo',
            renderer='foo.renderer',
        )

        self.addCleanup(reset_notification_channels)

    def test_cannot_create_instance(self):
        """
        BaseNotificationChannelProvider is an abstract class and we should not be able
        to create an instance of it
        """

        with self.assertRaises(TypeError):
            BaseNotificationChannelProvider()  # pylint: disable=abstract-class-instantiated

    def test_get_provider(self):
        """
        Makes sure we get an instance of the registered store provider
        """

        provider = get_notification_channel(self.test_user_id, self.test_msg_type)

        self.assertIsNotNone(provider)
        self.assertTrue(isinstance(provider, BaseDurableNotificationChannel))

        self.assertEqual(provider.name, 'channel6')
        self.assertEqual(provider.display_name, 'channel_name6')
        self.assertEqual(provider.display_description, 'channel_description6')

        # now verify that the wildcard hierarchy rules
        # work, by making a msg_type name which will match one of
        # the intermediate items in the hierarchy

        provider = get_notification_channel(
            self.test_user_id,
            NotificationType(
                name='edx_notifications.channels.tests.another_one',
                renderer='foo.renderer',
            )
        )

        self.assertEqual(provider.name, 'channel3')
        self.assertEqual(provider.display_name, 'channel_name3')
        self.assertEqual(provider.display_description, 'channel_description3')

        provider = get_notification_channel(
            self.test_user_id,
            NotificationType(
                name='edx_notifications.channels.diff_subpath.diff_leaf',
                renderer='foo.renderer',
            )
        )

        self.assertEqual(provider.name, 'channel2')
        self.assertEqual(provider.display_name, 'channel_name2')
        self.assertEqual(provider.display_description, 'channel_description2')

    @override_settings(NOTIFICATION_CHANNEL_PROVIDERS=None)
    def test_missing_provider_config(self):
        """
        Make sure we are throwing exceptions on poor channel configuration
        """

        with self.assertRaises(ImproperlyConfigured):
            get_notification_channel(self.test_user_id, self.test_msg_type)

    @override_settings(NOTIFICATION_CHANNEL_PROVIDER_TYPE_MAPS=None)
    def test_missing_maps_config(self):
        """
        Make sure we are throwing exceptions on poor channel mappings configuration
        """

        with self.assertRaises(ImproperlyConfigured):
            get_notification_channel(self.test_user_id, self.test_msg_type)

    @override_settings(NOTIFICATION_CHANNEL_PROVIDER_TYPE_MAPS={'edx_notifications.bogus': 'bogus'})
    def test_missing_global_mapping(self):
        """
        Make sure we are throwing exceptions when global mapping is missing
        """

        with self.assertRaises(ImproperlyConfigured):
            get_notification_channel(self.test_user_id, self.test_msg_type)

    @override_settings(NOTIFICATION_CHANNEL_PROVIDER_TYPE_MAPS={'*': 'bogus'})
    def test_bad_mapping(self):
        """
        Make sure we are throwing exceptions when a msg type is mapped to a channel name
        that does not exist
        """

        with self.assertRaises(ImproperlyConfigured):
            get_notification_channel(self.test_user_id, self.test_msg_type)

    @override_settings(NOTIFICATION_CHANNEL_PROVIDERS={"durable": {"class": "foo"}})
    def test_bad_provider_config(self):
        """
        Make sure we are throwing exceptions on poor configuration
        """

        with self.assertRaises(ImproperlyConfigured):
            get_notification_channel(self.test_user_id, self.test_msg_type)

    def test_bad_channel(self):
        """
        This will assert that a derived class from BaseChannelProvider which
        calls into the base will throw the NotImplementedError
        """

        with self.assertRaises(NotImplementedError):
            BadChannel().dispatch_notification_to_user(None, None)

        with self.assertRaises(NotImplementedError):
            BadChannel().bulk_dispatch_notification(None, None)

        with self.assertRaises(NotImplementedError):
            BadChannel().resolve_msg_link(None, None, None)

    def test_null_channel(self):
        """
        Makes sure that the NullNotificationChannel doesn't do anythign what so ever
        """

        test_msg_type = NotificationType(
            name='edx_notifications.channels.tests.test_channel.channeltests.null',
            renderer='foo.renderer',
        )

        provider = get_notification_channel(self.test_user_id, test_msg_type)

        self.assertIsNotNone(provider)
        self.assertTrue(isinstance(provider, NullNotificationChannel))

        self.assertIsNone(provider.dispatch_notification_to_user(None, None))
        self.assertEqual(provider.bulk_dispatch_notification(None, None), 0)

        self.assertIsNone(provider.resolve_msg_link(None, None, None))

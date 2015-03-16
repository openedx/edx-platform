"""
Module contains various XModule/XBlock services
"""
from django.conf import settings

import types

from xmodule.modulestore.django import modulestore


class SettingsService(object):
    """
    Allows server-wide configuration of XBlocks on a per-type basis

    XBlock settings are read from XBLOCK_SETTINGS settings key. Each XBlock is allowed access
    to single settings bucket. Bucket is determined by this service using the following rules:

    * Value of SettingsService.xblock_settings_bucket_selector is examined. If XBlock have attribute/property
    with the name of that value this attribute/property is read to get the bucket key (e.g. if XBlock have
    `block_settings_key = 'my_block_settings'`, bucket key would be 'my_block_settings').
    * Otherwise, XBlock class name is used

    Service is content-agnostic: it just returns whatever happen to be in the settings bucket (technically, it returns
    the bucket itself).

    If `default` argument is specified it is returned if:
    * There are no XBLOCK_SETTINGS setting
    * XBLOCK_SETTINGS is empty
    * XBLOCK_SETTINGS does not contain settings bucket

    If `default` is not specified or None, empty dictionary is used for default.

    Example:

        "XBLOCK_SETTINGS": {
            "my_block": {
                "setting1": 1,
                "setting2": []
            },
            "my_other_block": [1, 2, 3],
            "MyThirdBlock": "QWERTY"
        }

        class MyBlock:      block_settings_key='my_block'
        class MyOtherBlock: block_settings_key='my_other_block'
        class MyThirdBlock: pass
        class MissingBlock: pass

        service = SettingsService()
        service.get_settings_bucket(MyBlock())                      # { "setting1": 1, "setting2": [] }
        service.get_settings_bucket(MyOtherBlock())                 # [1, 2, 3]
        service.get_settings_bucket(MyThirdBlock())                 # "QWERTY"
        service.get_settings_bucket(MissingBlock())                 # {}
        service.get_settings_bucket(MissingBlock(), "default")      # "default"
        service.get_settings_bucket(MissingBlock(), None)           # {}
    """
    xblock_settings_bucket_selector = 'block_settings_key'

    def get_settings_bucket(self, block, default=None):
        """ Gets xblock settings dictionary from settings. """
        if not block:
            raise ValueError("Expected XBlock instance, got {0} of type {1}".format(block, type(block)))

        actual_default = default if default is not None else {}
        xblock_settings_bucket = getattr(block, self.xblock_settings_bucket_selector, block.unmixed_class.__name__)
        xblock_settings = settings.XBLOCK_SETTINGS if hasattr(settings, "XBLOCK_SETTINGS") else {}
        return xblock_settings.get(xblock_settings_bucket, actual_default)


class NotificationsService(object):
    """
    An xBlock service for xBlocks to talk to the Notification subsystem. This class basically introspects
    and exposes all functions in the Publisher and Consumer libraries, so it is a direct pass through.

    NOTE: This is a Singleton class. We should only have one instance of it!
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        This is the class factory to make sure this is a Singleton
        """
        if not cls._instance:
            cls._instance = super(NotificationsService, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """
        Class initializer, which just inspects the libraries and exposes the same functions
        as a direct pass through
        """
        import edx_notifications.lib.publisher as notifications_publisher_lib
        import edx_notifications.lib.consumer as notifications_consumer_lib
        self._bind_to_module_functions(notifications_publisher_lib)
        self._bind_to_module_functions(notifications_consumer_lib)

    def _bind_to_module_functions(self, module):
        """
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name, None)
            if isinstance(attr, types.FunctionType):
                if not hasattr(self, attr_name):
                    setattr(self, attr_name, attr)


class CoursewareParentInfoService(object):
    """
    An xBlock service that provides information about the courseware parent. This could be
    used for - say - generating breadcumbs
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        This is the class factory to make sure this is a Singleton
        """
        if not cls._instance:
            cls._instance = super(CoursewareParentInfoService, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def get_parent_info(self, module):
        """
        Returns the location and display name of the parent
        """

        parent_location = modulestore().get_parent_location(module)
        parent_module = modulestore().get_item(parent_location)

        return {
            'location': parent_location,
            'display_name': parent_module.display_name
        }


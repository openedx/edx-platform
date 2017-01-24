"""
Module contains various XModule/XBlock services
"""
from django.conf import settings


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

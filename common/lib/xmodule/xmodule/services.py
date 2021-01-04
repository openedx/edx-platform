"""
Module contains various XModule/XBlock services
"""


import inspect

from config_models.models import ConfigurationModel
from django.conf import settings
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


# TODO: ConfigurationService and its usage will be removed as a part of EDUCATOR-121
# reference: https://openedx.atlassian.net/browse/EDUCATOR-121
class ConfigurationService(object):
    """
    An XBlock service to talk with the Configuration Models. This service should provide
    a pathway to Configuration Model which is designed to configure the corresponding XBlock.
    """
    def __init__(self, configuration_model):
        """
        Class initializer, this exposes configuration model to XBlock.

        Arguments:
            configuration_model (ConfigurationModel): configurations for an XBlock

        Raises:
            exception (ValueError): when configuration_model is not a subclass of
            ConfigurationModel.
        """
        if not (inspect.isclass(configuration_model) and issubclass(configuration_model, ConfigurationModel)):
            raise ValueError(
                "Expected ConfigurationModel got {0} of type {1}".format(
                    configuration_model,
                    type(configuration_model)
                )
            )

        self.configuration = configuration_model


class TeamsConfigurationService(object):
    """
    An XBlock service that returns the teams_configuration object for a course.
    """
    def __init__(self):
        self._course = None

    def get_course(self, course_id):
        """
        Return the course instance associated with this TeamsConfigurationService.
        This default implementation looks up the course from the modulestore.
        """
        return modulestore().get_course(course_id)

    def get_teams_configuration(self, course_id):
        """
        Returns the team configuration for a given course.id
        """
        if not self._course:
            self._course = self.get_course(course_id)
        return self._course.teams_configuration

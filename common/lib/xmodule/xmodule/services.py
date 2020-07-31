"""
Module contains various XModule/XBlock services
"""


import inspect

from config_models.models import ConfigurationModel
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _
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


class CallToActionService:
    """
    An XBlock service that returns information on how to shift a learner's schedule.
    """
    CAPA_SUBMIT_DISABLED = 'capa_submit_disabled'
    VERTICAL_BANNER = 'vertical_banner'

    def get_ctas(self, xblock, category):
        """
        Return the calls to action associated with the specified category for the given xblock.

        See the CallToActionService class constants for a list of recognized categories.

        Returns: list of dictionaries, describing the calls to action, with the following keys:
                 link, link_name, form_values, and description.
                 If the category is not recognized, an empty list is returned.

        An example of a returned list:
        [{
            'link': 'localhost:18000/skip',
            'link_name': 'Skip this Problem',
            'form_values': {
                'foo': 'bar',
            },
            'description': "If you don't want to do this problem, just skip it!"
        }]
        """
        ctas = []

        if category == self.CAPA_SUBMIT_DISABLED:
            # xblock is a capa problem, and the submit button is disabled. Check if it's because of a personalized
            # schedule due date being missed, and if so, we can offer to shift it.
            if self._is_block_shiftable(xblock):
                ctas.append(self._make_reset_deadlines_cta(xblock))

        elif category == self.VERTICAL_BANNER:
            # xblock is a vertical, so we'll check all the problems inside it. If there are any that will show a
            # a "shift dates" CTA under CAPA_SUBMIT_DISABLED, then we'll also show the same CTA as a vertical banner.
            if any(self._is_block_shiftable(item) for item in xblock.get_display_items()):
                ctas.append(self._make_reset_deadlines_cta(xblock))

        return ctas

    @staticmethod
    def _is_block_shiftable(xblock):
        """
        Test if the xblock would be solvable if we were to shift dates.

        Only xblocks with an is_past_due method (e.g. capa and LTI) will be considered possibly shiftable.
        """
        if not hasattr(xblock, 'is_past_due'):
            return False

        if hasattr(xblock, 'attempts') and hasattr(xblock, 'max_attempts'):
            can_attempt = xblock.max_attempts is None or xblock.attempts < xblock.max_attempts
        else:
            can_attempt = True

        return xblock.self_paced and can_attempt and xblock.is_past_due()

    @staticmethod
    def _make_reset_deadlines_cta(xblock):
        from lms.urls import RESET_COURSE_DEADLINES_NAME
        return {
            'link': reverse(RESET_COURSE_DEADLINES_NAME),
            'link_name': _('Shift due dates'),
            'form_values': {
                'course_id': xblock.course_id,
            },
            'description': _('To participate in this assignment, the suggested schedule for your course needs '
                             'updating. Don’t worry, we’ll shift all the due dates for you and you won’t lose '
                             'any of your progress.'),
        }

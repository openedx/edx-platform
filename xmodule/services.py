"""
Module contains various XModule/XBlock services
"""


import inspect
import logging

from functools import partial

from config_models.models import ConfigurationModel
from django.conf import settings
from edx_when.field_data import DateLookupFieldData
from xblock.reference.plugins import Service
from xblock.runtime import KvsFieldData

from xmodule.modulestore.django import modulestore

from lms.djangoapps.courseware.field_overrides import OverrideFieldData
from lms.djangoapps.courseware.model_data import DjangoKeyValueStore, FieldDataCache
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from lms.djangoapps.lms_xblock.models import XBlockAsidesConfig


log = logging.getLogger(__name__)


class SettingsService:
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
            raise ValueError(f"Expected XBlock instance, got {block} of type {type(block)}")

        actual_default = default if default is not None else {}
        xblock_settings_bucket = getattr(block, self.xblock_settings_bucket_selector, block.unmixed_class.__name__)
        xblock_settings = settings.XBLOCK_SETTINGS if hasattr(settings, "XBLOCK_SETTINGS") else {}
        return xblock_settings.get(xblock_settings_bucket, actual_default)


# TODO: ConfigurationService and its usage will be removed as a part of EDUCATOR-121
# reference: https://openedx.atlassian.net/browse/EDUCATOR-121
class ConfigurationService:
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
                "Expected ConfigurationModel got {} of type {}".format(
                    configuration_model,
                    type(configuration_model)
                )
            )

        self.configuration = configuration_model


class TeamsConfigurationService:
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


class RebindUserServiceError(Exception):
    pass


class RebindUserService(Service):
    """
    An XBlock Service that allows modules to get rebound to real users if it was previously bound to an AnonymousUser.

    This used to be a local function inside the `lms.djangoapps.courseware.module_render.get_module_system_for_user`
    method, and was passed as a constructor argument to x_module.ModuleSystem. This has been refactored out into a
    service to simplify the ModuleSystem and lives in this module temporarily.

    TODO: Only the old LTI XBlock uses it in 2 places for LTI 2.0 integration. As the LTI XBlock is deprecated in
    favour of the LTI Consumer XBlock, this should be removed when the LTI XBlock is removed.

    Arguments:
        user (User) - A Django User object
        course_id (str) - Course ID
        course (Course) - Course Object
        get_module_system_for_user (function) - The helper function that will be called to create a module system
            for a specfic user. This is the parent function from which this service was reactored out.
            `lms.djangoapps.courseware.module_render.get_module_system_for_user`
        kwargs (dict) - all the keyword arguments that need to be passed to the `get_module_system_for_user`
            function when it is called during rebinding
    """
    def __init__(self, user, course_id, get_module_system_for_user, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.course_id = course_id
        self._ref = {
            "get_module_system_for_user": get_module_system_for_user
        }
        self._kwargs = kwargs

    def rebind_noauth_module_to_user(self, block, real_user):
        """
        Function that rebinds the module to the real_user.

        Will only work within a module bound to an AnonymousUser, e.g. one that's instantiated by the noauth_handler.

        Arguments:
            block (any xblock type):  the module to rebind
            real_user (django.contrib.auth.models.User):  the user to bind to

        Returns:
            nothing (but the side effect is that module is re-bound to real_user)
        """
        if self.user.is_authenticated:
            err_msg = "rebind_noauth_module_to_user can only be called from a module bound to an anonymous user"
            log.error(err_msg)
            raise RebindUserServiceError(err_msg)

        field_data_cache_real_user = FieldDataCache.cache_for_descriptor_descendents(
            self.course_id,
            real_user,
            block,
            asides=XBlockAsidesConfig.possible_asides(),
        )
        student_data_real_user = KvsFieldData(DjangoKeyValueStore(field_data_cache_real_user))

        with modulestore().bulk_operations(self.course_id):
            course = modulestore().get_course(course_key=self.course_id)

        (inner_system, inner_student_data) = self._ref["get_module_system_for_user"](
            user=real_user,
            student_data=student_data_real_user,  # These have implicit user bindings, rest of args considered not to
            descriptor=block,
            course_id=self.course_id,
            course=course,
            **self._kwargs
        )

        block.bind_for_student(
            inner_system,
            real_user.id,
            [
                partial(DateLookupFieldData, course_id=self.course_id, user=self.user),
                partial(OverrideFieldData.wrap, real_user, course),
                partial(LmsFieldData, student_data=inner_student_data),
            ],
        )

        block.scope_ids = block.scope_ids._replace(user_id=real_user.id)
        # now bind the module to the new ModuleSystem instance and vice-versa
        block.runtime = inner_system
        inner_system.xmodule_instance = block

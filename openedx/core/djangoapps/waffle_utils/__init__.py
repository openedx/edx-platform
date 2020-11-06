"""
Extra utilities for waffle: most classes are defined in edx_toggles.toggles (https://edx-toggles.readthedocs.io/), but
we keep here some extra classes for usage within edx-platform. These classes cover course override use cases.
"""
import logging
import warnings
from contextlib import contextmanager

from edx_django_utils.monitoring import set_custom_attribute
from edx_toggles.toggles import WaffleFlag as BaseWaffleFlag
from edx_toggles.toggles import WaffleFlagNamespace as BaseWaffleFlagNamespace
from edx_toggles.toggles import WaffleSwitch as BaseWaffleSwitch
from edx_toggles.toggles import WaffleSwitchNamespace as BaseWaffleSwitchNamespace
from opaque_keys.edx.keys import CourseKey

log = logging.getLogger(__name__)


class WaffleSwitchNamespace(BaseWaffleSwitchNamespace):
    """
    Deprecated class: instead, use edx_toggles.toggles.WaffleSwitchNamespace.
    """

    def __init__(self, name, log_prefix=None):
        super().__init__(name, log_prefix=log_prefix)
        warnings.warn(
            (
                "Importing WaffleSwitchNamespace from waffle_utils is deprecated. Instead, import from"
                " edx_toggles.toggles."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        set_custom_attribute("deprecated_waffle_utils", "WaffleSwitchNamespace[{}]".format(name))

    @contextmanager
    def override(self, switch_name, active=True):
        """
        Deprecated method: instead, use edx_toggles.toggles.testutils.override_waffle_switch.
        """
        warnings.warn(
            (
                "WaffleSwitchNamespace.override is deprecated. Instead, use"
                " edx_toggles.toggles.testutils.override_waffle_switch."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        set_custom_attribute(
            "deprecated_waffle_utils", "WaffleSwitchNamespace.override"
        )
        from edx_toggles.toggles.testutils import override_waffle_switch

        with override_waffle_switch(
            BaseWaffleSwitch(self, switch_name, module_name=__name__), active
        ):
            yield


class WaffleSwitch(BaseWaffleSwitch):
    """
    Deprecated class: instead, use edx_toggles.toggles.WaffleSwitch.
    """

    def __init__(self, waffle_namespace, switch_name, module_name=None):
        super().__init__(waffle_namespace, switch_name, module_name=module_name)
        warnings.warn(
            "Importing WaffleSwitch from waffle_utils is deprecated. Instead, import from edx_toggles.toggles.",
            DeprecationWarning,
            stacklevel=2,
        )
        set_custom_attribute("deprecated_waffle_utils", "WaffleSwitch[{}]".format(self.name))


class WaffleFlagNamespace(BaseWaffleFlagNamespace):
    """
    Deprecated class: instead, use edx_toggles.toggles.WaffleFlagNamespace.
    """

    def __init__(self, name, log_prefix=None):
        super().__init__(name, log_prefix=log_prefix)
        warnings.warn(
            "Importing WaffleFlagNamespace from waffle_utils is deprecated. Instead, import from edx_toggles.toggles.",
            DeprecationWarning,
            stacklevel=2,
        )
        set_custom_attribute("deprecated_waffle_utils", "WaffleFlagNamespace[{}]".format(name))


class WaffleFlag(BaseWaffleFlag):
    """
    Deprecated class: instead, use edx_toggles.toggles.WaffleFlag.
    """

    def __init__(self, waffle_namespace, flag_name, module_name=None):
        super().__init__(waffle_namespace, flag_name, module_name=module_name)
        warnings.warn(
            "Importing WaffleFlag from waffle_utils is deprecated. Instead, import from edx_toggles.toggles.",
            DeprecationWarning,
            stacklevel=2,
        )
        set_custom_attribute("deprecated_waffle_utils", "WaffleFlag[{}]".format(self.name))

    @contextmanager
    def override(self, active=True):
        """
        Deprecated method: instead, use edx_toggles.toggles.testutils.override_waffle_flag.
        """
        warnings.warn(
            (
                "WaffleFlag.override is deprecated. Instead, use"
                " edx_toggles.toggles.testutils.override_waffle_flag."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        set_custom_attribute("deprecated_waffle_utils", "WaffleFlag.override")
        from edx_toggles.toggles.testutils import override_waffle_flag

        with override_waffle_flag(self, active):
            yield


class CourseWaffleFlag(BaseWaffleFlag):
    """
    Represents a single waffle flag that can be forced on/off for a course. This class should be used instead of
    WaffleFlag when in the context of a course.

    Uses a cached waffle namespace.

    Usage:

       WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='my_namespace')
       SOME_COURSE_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'some_course_feature', __name__)

    And then we can check this flag in code with::

        SOME_COURSE_FLAG.is_enabled(course_key)

    The Django Admin "waffle_utils" section can be used to configure a course override for this same flag (e.g.
    my_namespace.some_course_feature).
    """

    def _get_course_override_value(self, course_key):
        """
        Returns True/False if the flag was forced on or off for the provided course. Returns None if the flag was not
        overridden.

        Note: Has side effect of caching the override value.

        Arguments:
            course_key (CourseKey): The course to check for override before checking waffle.
        """
        # Import is placed here to avoid model import at project startup.
        from .models import WaffleFlagCourseOverrideModel

        cache_key = "{}.{}".format(self.namespaced_flag_name, str(course_key))
        # pylint: disable=protected-access
        course_override = self.waffle_namespace._cached_flags.get(cache_key)

        if course_override is None:
            course_override = WaffleFlagCourseOverrideModel.override_value(
                self.namespaced_flag_name, course_key
            )
            # pylint: disable=protected-access
            self.waffle_namespace._cached_flags[cache_key] = course_override

        if course_override == WaffleFlagCourseOverrideModel.ALL_CHOICES.on:
            return True
        if course_override == WaffleFlagCourseOverrideModel.ALL_CHOICES.off:
            return False
        return None

    def is_enabled(self, course_key=None):  # pylint: disable=arguments-differ
        """
        Returns whether or not the flag is enabled within the context of a given course.

        Arguments:
            course_key (Optional[CourseKey]): The course to check for override before
                checking waffle. If omitted, check whether the flag is enabled
                outside the context of any course.
        """
        if course_key:
            assert isinstance(
                course_key, CourseKey
            ), "Provided course_key '{}' is not instance of CourseKey.".format(
                course_key
            )
        is_enabled_for_course = self._get_course_override_value(course_key)
        if is_enabled_for_course is not None:
            # pylint: disable=protected-access
            self.waffle_namespace._monitor_value(
                self.namespaced_flag_name, is_enabled_for_course
            )
            return is_enabled_for_course
        return super().is_enabled()

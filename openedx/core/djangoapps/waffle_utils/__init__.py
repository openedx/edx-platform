"""
Extra utilities for waffle: most classes are defined in edx_toggles.toggles, but we keep here some extra classes for
usage within edx-platform. These classes cover course override use cases.


Usage:

   WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='my_namespace')
   # Use CourseWaffleFlag when you are in the context of a course.
   SOME_COURSE_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'some_course_feature', __name__)

You can check this flag in code using the following::

    SOME_COURSE_FLAG.is_enabled(course_key)

To test WaffleSwitchNamespace, use the provided context managers.  For example:

    with WAFFLE_SWITCHES.override(waffle.ESTIMATE_FIRST_ATTEMPTED, active=True):
        ...

Also see ``WAFFLE_FLAG_CUSTOM_ATTRIBUTES`` and docstring for _set_waffle_flag_attribute
for temporarily instrumenting/monitoring waffle flag usage.

"""
import logging
from contextlib import contextmanager

from opaque_keys.edx.keys import CourseKey

from edx_toggles.toggles import WaffleFlag as BaseWaffleFlag
from edx_toggles.toggles import WaffleFlagNamespace
from edx_toggles.toggles import WaffleSwitch as BaseWaffleSwitch
from edx_toggles.toggles import WaffleSwitchNamespace as BaseWaffleSwitchNamespace

log = logging.getLogger(__name__)


class WaffleSwitchNamespace(BaseWaffleSwitchNamespace):
    """
    Waffle switch namespace that implements custom overriding methods. We should eventually get rid of this class.
    """

    @contextmanager
    def override(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the duration of this
        contextmanager.
        Note: The value is overridden in the request cache AND in the model.
        """
        previous_active = self.is_enabled(switch_name)
        try:
            self.override_for_request(switch_name, active)
            with self.override_in_model(switch_name, active):
                yield
        finally:
            self.override_for_request(switch_name, previous_active)

    def override_for_request(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the remainder of
        this request (as this is not a context manager).
        Note: The value is overridden in the request cache, not in the model.
        """
        namespaced_switch_name = self._namespaced_name(switch_name)
        self._cached_switches[namespaced_switch_name] = active
        log.info(
            "%sSwitch '%s' set to %s for request.",
            self.log_prefix,
            namespaced_switch_name,
            active,
        )

    @contextmanager
    def override_in_model(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the duration of this
        contextmanager.
        Note: The value is overridden in the model, not the request cache.
        Note: This should probably be moved to a test class.
        """
        # Import is placed here to avoid model import at project startup.
        # pylint: disable=import-outside-toplevel
        from waffle.testutils import override_switch as waffle_override_switch

        namespaced_switch_name = self._namespaced_name(switch_name)
        with waffle_override_switch(namespaced_switch_name, active):
            log.info(
                "%sSwitch '%s' set to %s in model.",
                self.log_prefix,
                namespaced_switch_name,
                active,
            )
            yield


class WaffleSwitch(BaseWaffleSwitch):
    """
    This class should be removed in favour of edx_toggles.toggles.WaffleSwitch once we get rid of the
    WaffleSwitchNamespace class.
    """

    NAMESPACE_CLASS = WaffleSwitchNamespace

    @contextmanager
    def override(self, active=True):
        with self.waffle_namespace.override(self.switch_name, active):
            yield


class WaffleFlag(BaseWaffleFlag):
    """
    Waffle flag class that implements custom override method.

    This class should be removed in favour of edx_toggles.toggles.WaffleFlag once we get rid of the WaffleFlagNamespace
    class and the `override` method.
    """

    @contextmanager
    def override(self, active=True):
        """
        Shortcut method for `override_waffle_flag`.
        """
        # TODO We can move this import to the top of the file once this code is
        # not all contained within the __init__ module.
        from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag

        with override_waffle_flag(self, active):
            yield


class CourseWaffleFlag(WaffleFlag):
    """
    Represents a single waffle flag that can be forced on/off for a course.

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
            self.NAMESPACE_CLASS._monitor_value(
                self.namespaced_flag_name, is_enabled_for_course
            )
            return is_enabled_for_course
        return super().is_enabled()

"""
Extra utilities for waffle: most classes are defined in edx_toggles.toggles (https://edx-toggles.readthedocs.io/), but
we keep here some extra classes for usage within edx-platform. These classes cover course override use cases.
"""
import logging

from opaque_keys.edx.keys import CourseKey

# pylint: disable=unused-import
from edx_toggles.toggles import WaffleFlag, WaffleFlagNamespace, WaffleSwitch, WaffleSwitchNamespace

log = logging.getLogger(__name__)


class CourseWaffleFlag(WaffleFlag):
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
            self.NAMESPACE_CLASS._monitor_value(
                self.namespaced_flag_name, is_enabled_for_course
            )
            return is_enabled_for_course
        return super().is_enabled()

"""
Extra utilities for waffle: most classes are defined in edx_toggles.toggles (https://edx-toggles.readthedocs.io/), but
we keep here some extra classes for usage within edx-platform. These classes cover course override use cases.
"""
import logging

from edx_django_utils.monitoring import set_custom_attribute
from openedx.core.djangoapps.waffle_utils.__future__ import FutureCourseWaffleFlag

log = logging.getLogger(__name__)


class CourseWaffleFlag(FutureCourseWaffleFlag):
    """
    Represents a single waffle flag that can be forced on/off for a course.

    Deprecated: use the FutureCourseWaffleFlag instead.
    """
    def __init__(self, waffle_namespace, flag_name, module_name=None):
        log_prefix = ""
        if not isinstance(waffle_namespace, str):
            log_prefix = waffle_namespace.log_prefix or log_prefix
            waffle_namespace = waffle_namespace.name

        # Non-namespaced flag_name attribute preserved for backward compatibility
        self._flag_name = flag_name
        name = f"{waffle_namespace}.{flag_name}"
        super().__init__(name, module_name=module_name, log_prefix=log_prefix)
        set_custom_attribute(
            "deprecated_legacy_waffle_class",
            f"{self.__class__.__module__}.{self.__class__.__name__}[{self.name}]"
        )

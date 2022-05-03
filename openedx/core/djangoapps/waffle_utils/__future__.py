"""
Temporary module to switch from the LegacyWaffle* classes.
"""
from edx_django_utils.monitoring import set_custom_attribute

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag


class FutureCourseWaffleFlag(CourseWaffleFlag):
    """
    Temporary class to support ORA transition to the modern CourseWaffleFlag.
    """
    def __init__(self, name, module_name, log_prefix=""):
        super().__init__(name, module_name=module_name, log_prefix=log_prefix)
        set_custom_attribute(
            "deprecated_legacy_waffle_class",
            f"{self.__class__.__module__}.{self.__class__.__name__}[{self.name}]"
        )

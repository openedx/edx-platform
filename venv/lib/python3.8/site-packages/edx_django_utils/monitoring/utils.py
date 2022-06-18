"""
Deprecated monitoring helpers for backward-compatibility.

IMPORTANT: No new code should be added to this file.
TODO: Remove this file once this code are no longer used.

"""
import warnings

from .internal.utils import accumulate as internal_accumulate
from .internal.utils import increment as internal_increment
from .internal.utils import set_custom_attribute as internal_set_custom_attribute
from .internal.utils import set_custom_attributes_for_course_key as internal_set_custom_attributes_for_course_key


def accumulate(name, value):
    """
    Deprecated method. Use public API instead.
    """
    msg = "Use 'monitoring.accumulate' in place of 'monitoring.utils.accumulate'."
    warnings.warn(msg, DeprecationWarning)
    internal_set_custom_attribute('deprecated_monitoring_utils', f'accumulate[{name}]')
    internal_accumulate(name, value)


def increment(name):
    """
    Deprecated method. Use public API instead.
    """
    msg = "Use 'monitoring.increment' in place of 'monitoring.utils.increment'."
    warnings.warn(msg, DeprecationWarning)
    internal_set_custom_attribute('deprecated_monitoring_utils', f'increment[{name}]')
    internal_increment(name)


def set_custom_attribute(key, value):
    """
    Deprecated method. Use public API instead.
    """
    msg = "Use 'monitoring.set_custom_attribute' in place of 'monitoring.utils.set_custom_attribute'."
    warnings.warn(msg, DeprecationWarning)
    internal_set_custom_attribute('deprecated_monitoring_utils', f'set_custom_attribute[{key}]')
    internal_set_custom_attribute(key, value)


def set_custom_attributes_for_course_key(course_key):
    """
    Deprecated method. Use public API instead.
    """
    msg = "Use 'monitoring.set_custom_attributes_for_course_key' in place of " \
          "'monitoring.utils.set_custom_attributes_for_course_key'."
    warnings.warn(msg, DeprecationWarning)
    internal_set_custom_attribute(
        'deprecated_monitoring_utils',
        'set_custom_attributes_for_course_key[{}]'.format(str(course_key))
    )
    internal_set_custom_attributes_for_course_key(course_key)


def set_custom_metric(key, value):  # pragma: no cover
    """
    Deprecated method to set monitoring custom attribute.
    """
    msg = "Use 'set_custom_attribute' in place of 'set_custom_metric'."
    warnings.warn(msg, DeprecationWarning)
    internal_set_custom_attribute('deprecated_monitoring_utils', f'set_custom_metric[{key}]')
    internal_set_custom_attribute(key, value)


def set_custom_metrics_for_course_key(course_key):  # pragma: no cover
    """
    Deprecated method to set monitoring custom attributes for course key.
    """
    msg = "Use 'set_custom_attributes_for_course_key' in place of 'set_custom_metrics_for_course_key'."
    warnings.warn(msg, DeprecationWarning)
    internal_set_custom_attribute(
        'deprecated_monitoring_utils',
        'set_custom_metrics_for_course_key[{}]'.format(str(course_key))
    )
    internal_set_custom_attributes_for_course_key(course_key)

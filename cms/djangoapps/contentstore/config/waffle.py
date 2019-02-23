"""
This module contains various configuration settings via
waffle switches for the contentstore app.
"""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace, WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = 'studio'

# Switches
ENABLE_ACCESSIBILITY_POLICY_PAGE = 'enable_policy_page'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle Switch class for Studio pages.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix='Studio: ')


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle Flag class for Studio pages.
    """
    return WaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix='Studio: ')

# Flags
ENABLE_PROCTORING_PROVIDER_OVERRIDES = CourseWaffleFlag(
    waffle_namespace=waffle_flags(),
    flag_name='enable_proctoring_provider_overrides',
    flag_undefined_default=False
)

ENABLE_CHECKLISTS_QUALITY = CourseWaffleFlag(
    waffle_namespace=waffle_flags(),
    flag_name='enable_checklists_quality',
    flag_undefined_default=True
)

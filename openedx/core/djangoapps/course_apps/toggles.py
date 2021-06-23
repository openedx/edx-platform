"""
Toggles for course apps.
"""
from edx_toggles.toggles import LegacyWaffleSwitchNamespace

#: Namespace for use by course apps for creating availability toggles
COURSE_APPS_WAFFLE_NAMESPACE = LegacyWaffleSwitchNamespace("course_apps")

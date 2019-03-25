"""
Student app helpers and settings
"""
from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace


# Namespace for student app waffle switches
STUDENT_WAFFLE_NAMESPACE = WaffleSwitchNamespace(name='student')

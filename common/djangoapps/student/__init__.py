"""
Student app helpers and settings
"""


from edx_toggles.toggles import LegacyWaffleSwitchNamespace

# Namespace for student app waffle switches
STUDENT_WAFFLE_NAMESPACE = LegacyWaffleSwitchNamespace(name='student')

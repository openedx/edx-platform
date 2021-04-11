"""
Student app helpers and settings
"""


from edx_toggles.toggles import WaffleSwitchNamespace

# Namespace for student app waffle switches
STUDENT_WAFFLE_NAMESPACE = WaffleSwitchNamespace(name='student')

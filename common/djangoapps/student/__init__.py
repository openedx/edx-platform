"""
Student app helpers and settings
"""
from __future__ import absolute_import

from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

# Namespace for student app waffle switches
STUDENT_WAFFLE_NAMESPACE = WaffleSwitchNamespace(name='student')

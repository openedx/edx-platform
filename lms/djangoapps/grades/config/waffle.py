"""
This module contains various configuration settings via
waffle switches for the Grades app.
"""
from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = u'grades'

# Switches
WRITE_ONLY_IF_ENGAGED = u'write_only_if_engaged'
ASSUME_ZERO_GRADE_IF_ABSENT = u'assume_zero_grade_if_absent'
ESTIMATE_FIRST_ATTEMPTED = u'estimate_first_attempted'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Grades.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Grades: ')

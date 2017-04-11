"""
This module contains various configuration settings via
waffle switches for the Grades app.
"""
from openedx.core.djangolib.waffle_utils import WaffleSwitchPlus


# Namespace
WAFFLE_NAMESPACE = u'grades'

# Switches
WRITE_ONLY_IF_ENGAGED = u'write_only_if_engaged'
ASSUME_ZERO_GRADE_IF_ABSENT = u'assume_zero_grade_if_absent'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Grades.
    """
    return WaffleSwitchPlus(namespace=WAFFLE_NAMESPACE, log_prefix=u'Grades: ')

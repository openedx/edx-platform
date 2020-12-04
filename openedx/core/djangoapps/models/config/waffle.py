"""
This module contains various configuration settings via
waffle switches for the course_details view.
"""


from edx_toggles.toggles import WaffleFlagNamespace, WaffleSwitchNamespace
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

COURSE_DETAIL_WAFFLE_NAMESPACE = 'course_detail'
COURSE_DETAIL_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=COURSE_DETAIL_WAFFLE_NAMESPACE)
WAFFLE_SWITCHES = WaffleSwitchNamespace(name=COURSE_DETAIL_WAFFLE_NAMESPACE)

# Course Override Flag
COURSE_DETAIL_UPDATE_CERTIFICATE_DATE = u'course_detail_update_certificate_date'


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for course detail.
    """
    return {
        COURSE_DETAIL_UPDATE_CERTIFICATE_DATE: CourseWaffleFlag(
            waffle_namespace=COURSE_DETAIL_WAFFLE_NAMESPACE,
            flag_name=COURSE_DETAIL_UPDATE_CERTIFICATE_DATE,
            module_name=__name__,
        )
    }


def enable_course_detail_update_certificate_date(course_id):
    """
    Returns True if course_detail_update_certificate_date course override flag is enabled,
    otherwise False.
    """
    return waffle_flags()[COURSE_DETAIL_UPDATE_CERTIFICATE_DATE].is_enabled(course_id)

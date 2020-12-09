"""
Courseware API Mixins.
"""

from babel.numbers import get_currency_symbol

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.courseware.utils import can_show_verified_upgrade, verified_upgrade_deadline_link
from openedx.features.course_duration_limits.access import get_user_course_expiration_date


def serialize_upgrade_info(user, course_overview, enrollment):
    """
    Return verified mode upgrade information, or None.

    This is used in a few API views to provide consistent upgrade info to frontends.
    """
    if not can_show_verified_upgrade(user, enrollment):
        return None

    mode = CourseMode.verified_mode_for_course(course=course_overview)
    return {
        'access_expiration_date': get_user_course_expiration_date(user, course_overview),
        'currency': mode.currency.upper(),
        'currency_symbol': get_currency_symbol(mode.currency.upper()),
        'price': mode.min_price,
        'sku': mode.sku,
        'upgrade_url': verified_upgrade_deadline_link(user, course_overview),
    }

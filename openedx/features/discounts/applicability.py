# -*- coding: utf-8 -*-
"""
Contains code related to computing discount percentage
and discount applicability.

WARNING:
Keep in mind that the code in this file only applies to discounts controlled in the lms like the first purchase offer,
not other discounts like coupons or enterprise/program offers configured in ecommerce.

"""
from openedx.core.djangoapps.course_modes.models import CourseMode
from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace

# .. feature_toggle_name: discounts.enable_discounting
# .. feature_toggle_type: flag
# .. feature_toggle_default: False
# .. feature_toggle_description: Toggle discounts always being disabled
# .. feature_toggle_category: discounts
# .. feature_toggle_use_cases: monitored_rollout
# .. feature_toggle_creation_date: 2019-4-16
# .. feature_toggle_expiration_date: None
# .. feature_toggle_warnings: None
# .. feature_toggle_tickets: REVEM-282
# .. feature_toggle_status: supported
DISCOUNT_APPLICABILITY_FLAG = WaffleFlag(
    waffle_namespace=WaffleFlagNamespace(name=u'discounts'),
    flag_name=u'enable_discounting',
    flag_undefined_default=False
)


def can_receive_discount(user, course):  # pylint: disable=unused-argument
    """
    Check all the business logic about whether this combination of user and course
    can receive a discount.
    """
    # Always disable discounts until we are ready to enable this feature
    if not DISCOUNT_APPLICABILITY_FLAG.is_enabled():
        return False

    # TODO: Add additional conditions to return False here

    # Course end date needs to be in the future
    if course.has_ended():
        return False

    # Course needs to have a non-expired verified mode
    modes_dict = CourseMode.modes_for_course_dict(course=course, include_expired=False)
    verified_mode = modes_dict.get('verified', None)
    if not verified_mode:
        return False

    return True


def discount_percentage():
    """
    Get the configured discount amount.
    """
    # TODO: Add configuration information here
    return 15

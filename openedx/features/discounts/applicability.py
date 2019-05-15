# -*- coding: utf-8 -*-
"""
Contains code related to computing discount percentage
and discount applicability.
"""
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


def can_receive_discount(user, course_key_string):  # pylint: disable=unused-argument
    """
    Check all the business logic about whether this combination of user and course
    can receive a discount.
    """
    # Always disable discounts until we are ready to enable this feature
    if not DISCOUNT_APPLICABILITY_FLAG.is_enabled():
        return False

    # TODO: Add additional conditions to return False here

    return True


def discount_percentage():
    """
    Get the configured discount amount.
    """
    # TODO: Add configuration information here
    return 15

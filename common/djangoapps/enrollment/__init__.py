"""
Enrollment API helpers and settings
"""
from openedx.core.djangoapps.waffle_utils import (WaffleFlag, WaffleFlagNamespace)

WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='enrollment_api_rate_limit')

REDUCE_RATE_LIMIT_FOR_STAFF_FOR_ENROLLMENT_API = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'reduce_staff_rate_limit')
USE_UNIVERSAL_RATE_LIMIT_FOR_ENROLLMENT_API = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'use_universal_rate_limit')

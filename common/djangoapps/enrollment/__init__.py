"""
Enrollment API helpers and settings
"""
from openedx.core.djangoapps.waffle_utils import (WaffleFlag, WaffleFlagNamespace)

WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='enrollment_api_rate_limit')

USE_RATE_LIMIT_400_FOR_STAFF_FOR_ENROLLMENT_API = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'staff_rate_limit_400')
USE_RATE_LIMIT_100_FOR_STAFF_FOR_ENROLLMENT_API = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'staff_rate_limit_100')
USE_RATE_LIMIT_40_FOR_ENROLLMENT_API = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'rate_limit_40')

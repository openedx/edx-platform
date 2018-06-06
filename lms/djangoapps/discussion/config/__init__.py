"""
Discussion settings and flags.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlag, WaffleFlagNamespace

# Namespace for course experience waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='edx_discussions')

# Waffle flag to enable the use of Bootstrap
USE_BOOTSTRAP_FLAG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'use_bootstrap')

# Course waffle flag for automatic profanity checking
PROFANITY_CHECKER_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'profanity_checker')

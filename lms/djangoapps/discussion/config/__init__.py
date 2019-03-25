"""
Discussion settings and flags.
"""

from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace

# Namespace for course experience waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='edx_discussions')

# Waffle flag to enable the use of Bootstrap
USE_BOOTSTRAP_FLAG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'use_bootstrap', flag_undefined_default=True)

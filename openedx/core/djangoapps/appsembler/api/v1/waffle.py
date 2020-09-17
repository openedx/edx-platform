"""
Waffle flags for Tahoe v1 APIs.
"""

from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace

WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='appsembler_api_v1')

# Fix the Enrollment API results bug gradually
# TODO: RED-1387: Remove this flag after release
FIX_ENROLLMENT_RESULTS_BUG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'fix_enrollment_results_bug',
                                        flag_undefined_default=False)

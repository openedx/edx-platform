"""
Portfolio project helpers and settings
"""
from openedx.core.djangoapps.waffle_utils import (
    CourseWaffleFlag, WaffleFlag, WaffleFlagNamespace
)

# Namespace for portfolio project waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='portfolio_project')


# https://openedx.atlassian.net/browse/LEARNER-3926
INCLUDE_PORTFOLIO_UPSELL_MODAL = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'include_upsell_modal')

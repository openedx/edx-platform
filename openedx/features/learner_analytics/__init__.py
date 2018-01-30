"""
Learner analytics helpers and settings
"""
from openedx.core.djangoapps.waffle_utils import (
    CourseWaffleFlag, WaffleFlag, WaffleFlagNamespace
)

# Namespace for learner analytics waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='learner_analytics')

# Simple safety valve in case the modal breaks DOM.
INCLUDE_UPSELL_MODAL = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'include_upsell_modal')

# Enables the learner analytics page for different courses via waffle course overrides.
ENABLE_DASHBOARD_TAB = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'enable_dashboard_tab')

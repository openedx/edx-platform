"""
Learner analytics helpers and settings
"""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace


# Namespace for learner analytics waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='learner_analytics')

ENABLE_DASHBOARD_TAB = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'enable_dashboard_tab')

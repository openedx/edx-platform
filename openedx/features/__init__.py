"""
Learner profile settings and helper methods.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace


# Namespace for learner profile waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='learner_profile')

# Waffle flag to show achievements on the learner profile.
SHOW_ACHIEVEMENTS_FLAG = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'show_achievements')

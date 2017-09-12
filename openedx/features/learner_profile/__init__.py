"""
Learner profile settings and helper methods.
"""

from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace


# Namespace for learner profile waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='learner_profile')

# Waffle flag to show achievements on the learner profile.
# TODO: LEARNER-2443: 08/2017: Remove flag after rollout.
SHOW_ACHIEVEMENTS_FLAG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'show_achievements')

# Waffle flag for showing a message about the new profile features.
# TODO: LEARNER-2554: 09/2017: Remove flag once message is no longer needed.
SHOW_PROFILE_MESSAGE = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'show_message')

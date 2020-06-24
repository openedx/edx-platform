"""
Discussion settings and flags.
"""

from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace

ENABLE_FORUM_DAILY_DIGEST = 'enable_forum_daily_digest'


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for Grades.
    """
    namespace = WaffleFlagNamespace(name='edx_discussions')
    return {
        # By default, enable forum notifications. Can be disabled platform wide.
        ENABLE_FORUM_DAILY_DIGEST: WaffleFlag(
            namespace,
            ENABLE_FORUM_DAILY_DIGEST,
            flag_undefined_default=True
        ),
    }


def is_forum_daily_digest_enabled():
    """Returns whether forum notification features should be visible"""
    return waffle_flags()[ENABLE_FORUM_DAILY_DIGEST].is_enabled()

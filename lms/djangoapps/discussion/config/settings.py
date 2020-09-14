"""
Discussion settings.
"""
from django.conf import settings

# .. toggle_name: FEATURES['ENABLE_FORUM_DAILY_DIGEST']
# .. toggle_implementation: DjangoSetting
# .. toggle_default: True
# .. toggle_description: Settings for forums/discussions to on/off daily digest
#   feature. Set this to True if you want to enable users to subscribe and unsubscribe
#   for daily digest. This setting enables deprecation of daily digest.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2020-03-09
ENABLE_FORUM_DAILY_DIGEST = 'enable_forum_daily_digest'


def is_forum_daily_digest_enabled():
    """Returns whether forum notification features should be visible"""
    return settings.FEATURES.get('ENABLE_FORUM_DAILY_DIGEST', True)

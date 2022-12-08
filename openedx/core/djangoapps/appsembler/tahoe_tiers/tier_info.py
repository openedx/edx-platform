"""
Tier helper and calculation classes with no model dependency.

Note: This is cloned from `django-tiers:tiers.tier_info.py` to prepare for removing/refactoring the dependency.
"""
from collections import namedtuple

from django.utils import timezone
from django.utils.timesince import timeuntil

TierTuple = namedtuple('TierTuple', ['id', 'name'])


class TierInfo:
    """
    Tier info and calculator class.

    TODO: Move into the Site Configuration Client package.
    """

    TRIAL = TierTuple('trial', 'Trial')  # Expires in 30 days
    BASIC = TierTuple('basic', 'Basic')
    PRO = TierTuple('pro', 'Professional')
    PREMIUM = TierTuple('premium', 'Premium')

    TIERS = (
        TRIAL,
        BASIC,
        PRO,
        PREMIUM,
    )

    def __init__(self, tier, subscription_ends, always_active):
        self.tier = tier
        self.subscription_ends = subscription_ends
        self.always_active = always_active

    def has_subscription_ended(self, now=None):
        """Helper function that checks whether a subscription has expired"""
        if self.always_active:
            return False

        if not now:
            now = timezone.now()

        return now > self.subscription_ends

    def should_show_expiration_warning(self):
        """Decide if expiration warning is needed."""
        if self.always_active:
            return False

        return self.tier == self.TRIAL.id

    def time_til_expiration(self, now=None):
        """Pretty prints time left til expiration"""
        if self.always_active:
            return False

        if not now:
            now = timezone.now()

        return timeuntil(self.subscription_ends, now)

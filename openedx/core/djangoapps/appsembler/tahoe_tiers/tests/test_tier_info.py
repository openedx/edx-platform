"""
Tests for the TierInfo helper class.
"""

from datetime import timedelta
from django.utils.timezone import now
from ..tier_info import TierInfo


def tier_info_factory(
    tier=TierInfo.TRIAL,
    subscription_ends=now() + timedelta(days=30),
    always_active=False,
):
    return TierInfo(
        tier=tier,
        subscription_ends=subscription_ends,
        always_active=always_active,
    )


def test_non_expired_tier():
    t = tier_info_factory()
    assert not t.always_active
    assert not t.has_subscription_ended()


def test_expired_tier():
    t = tier_info_factory(subscription_ends=(now() - timedelta(days=2)))
    assert not t.always_active
    assert t.has_subscription_ended()


def test_exemption():
    t = tier_info_factory(
        always_active=True,
        subscription_ends=(now() - timedelta(days=20)),
    )
    assert t.always_active
    assert not t.has_subscription_ended()

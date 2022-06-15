"""
Factories and fixtures for pytest.
"""

import pytest

from django.utils import timezone

from tiers.tier_info import TierInfo


@pytest.fixture
def tier_info():
    """
    TierInfo fixture.
    """
    return TierInfo(
        tier='trial',
        always_active=False,
        subscription_ends=timezone.now(),
    )

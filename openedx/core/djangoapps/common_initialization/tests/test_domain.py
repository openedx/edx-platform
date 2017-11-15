"""Tests for domain logic in openedx/core/djangoapps/common_initialization/apps.py"""

from openedx.core.djangoapps.common_initialization.apps import acceptable_domain_name

import pytest


@pytest.mark.parametrize("domain, result", [
    ("mysite.com", True),
    ("mysite.com:8000", True),
    ("edx.someguy.org", False),
    ("openedx.someguy.org", True),
    ("courses.edx.someguy.org", False),
    ("courses.edx.someguy.org:18010", False),
])
def test_acceptable_domain_name(domain, result):
    assert acceptable_domain_name(domain) == result

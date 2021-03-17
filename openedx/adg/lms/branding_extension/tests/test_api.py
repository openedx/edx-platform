"""
Tests of extended Branding API
"""
from django.urls import reverse

from ..api import get_home_url


def test_home_url():
    """
    Test API end-point for retrieving the header
    """
    expected_url = get_home_url()
    assert reverse('root') == expected_url

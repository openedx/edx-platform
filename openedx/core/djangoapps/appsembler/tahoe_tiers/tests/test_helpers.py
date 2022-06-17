"""
Tests for helper functions.
"""
import pytest
from unittest.mock import patch

from django.test import RequestFactory

from organizations.tests.factories import OrganizationFactory

from openedx.core.djangoapps.appsembler.tahoe_tiers.helpers import (
    TIER_INFO_REQUEST_FIELD_NAME,
    get_tier_info,
)

from .conftest import tier_info


def test_get_tier_info_unavailable():
    """
    Test the `get_tier_info` helper for complete missing TierInfo.
    """
    request = RequestFactory().get('/dashboard')
    request.session = {}

    actual_tier_info = get_tier_info(request)

    assert actual_tier_info is None, 'Because no organization is associated with the request'
    assert hasattr(request, TIER_INFO_REQUEST_FIELD_NAME)
    assert getattr(request, TIER_INFO_REQUEST_FIELD_NAME) is None


def test_get_tier_info_from_request_cache(tier_info):
    """
    Test the `get_tier_info` helper for using the `_tahoe_tier_info`.
    """
    request = RequestFactory().get('/dashboard')
    setattr(request, TIER_INFO_REQUEST_FIELD_NAME, tier_info)

    actual_tier_info = get_tier_info(request)

    assert actual_tier_info == tier_info, 'Should return from request `_tahoe_tier_info` property'
    assert getattr(request, TIER_INFO_REQUEST_FIELD_NAME) == tier_info, 'should cache it'


@pytest.mark.django_db
@patch('openedx.core.djangoapps.appsembler.tahoe_tiers.helpers.get_amc_tier_info_from_organization')
def test_get_tier_info_from_amc(mock_get_amc_tier_info, tier_info):
    """
    Test the `get_tier_info` helper for using the `_tahoe_tier_info`.
    """
    request = RequestFactory().get('/dashboard')
    organization = OrganizationFactory.create()
    request.session = {'organization': organization}
    mock_get_amc_tier_info.return_value = tier_info

    actual_tier_info = get_tier_info(request)

    assert actual_tier_info == tier_info, 'Should return AMC tiers'
    mock_get_amc_tier_info.assert_called_once_with(organization)
    assert getattr(request, TIER_INFO_REQUEST_FIELD_NAME) == tier_info, 'should cache it'


@patch('openedx.core.djangoapps.appsembler.tahoe_tiers.helpers.get_current_site_config_tier_info')
def test_get_tier_info_from_site_config(mock_get_site_config_tier_info, tier_info):
    """
    Test the `get_tier_info` helper for using the `_tahoe_tier_info`.
    """
    request = RequestFactory().get('/dashboard')
    request.session = {}
    mock_get_site_config_tier_info.return_value = tier_info

    actual_tier_info = get_tier_info(request)

    assert actual_tier_info == tier_info, 'Should return from Site Config adapter'
    assert getattr(request, TIER_INFO_REQUEST_FIELD_NAME) == tier_info, 'should cache it'

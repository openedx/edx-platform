"""
All the tests for utilities of Django sites
"""
import pytest
from mock import patch

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.features.philu_utils.sites import get_site


@pytest.mark.django_db
def test_get_site_successfully():
    """
    Assert that site exists and returned successfully
    """
    site = SiteFactory()
    assert site == get_site(site.id)


@pytest.mark.django_db
@patch('openedx.features.philu_utils.sites.log.error')
def test_get_site_site_not_found(mock_log_error):
    """
    Assert that site does not exists
    """
    site = get_site(200)
    assert site is None
    assert mock_log_error.called_once

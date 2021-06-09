"""
Tests for helpers of branding_extension app
"""
import mock
import pytest
from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse
from freezegun import freeze_time

from openedx.adg.lms.branding_extension.constants import TARGET_BLANK, TARGET_SELF
from openedx.adg.lms.branding_extension.helpers import (
    get_copyright,
    get_footer_navigation_links,
    is_referred_by_login_or_register
)


def test_get_footer_navigation_links(mocker):
    """
    Tests `get_footer_navigation_links` helper method of branding extension
    """
    test_url = 'test_url'
    mocker.patch('openedx.adg.lms.branding_extension.helpers.marketing_link', return_value=test_url)

    branding_links = get_footer_navigation_links()
    assert len(branding_links) == 5
    assert branding_links == [
        {
            'url': test_url,
            'title': 'About',
            'target': TARGET_SELF,
        },
        {
            'url': reverse('our_team'),
            'title': 'Our Team',
            'target': TARGET_SELF,
        },
        {
            'url': test_url,
            'title': 'Contact',
            'target': TARGET_SELF,
        },
        {
            'url': settings.SUPPORT_LINK,
            'title': 'Support',
            'target': TARGET_BLANK,
        },
        {
            'url': test_url,
            'title': 'Terms',
            'target': TARGET_SELF,
        },
    ]


@freeze_time('2021-02-01')
def test_get_copyright(mocker):
    """
    Tests `get_copyright` helper method of branding extension
    """
    test_platform_name = 'test'
    mocker.patch(
        'openedx.adg.lms.branding_extension.helpers.configuration_helpers.get_value',
        return_value=test_platform_name
    )

    assert get_copyright() == '\u00A9 {} {}'.format(2021, test_platform_name)


def test_is_referred_by_login_or_register_in_testing_environment():
    request = RequestFactory().request()
    flag = is_referred_by_login_or_register(request)

    assert flag is True


@mock.patch('openedx.adg.lms.branding_extension.helpers.is_testing_environment')
def test_is_referred_by_login_or_register_with_no_referred_value(mock_is_testing_environment):
    mock_is_testing_environment.return_value = False

    request = RequestFactory().request()
    flag = is_referred_by_login_or_register(request)

    assert flag is False


@mock.patch('openedx.adg.lms.branding_extension.helpers.is_testing_environment')
@pytest.mark.parametrize(
    'path, expected_value',
    [('login', True), ('register', True), ('dashboard', False)],
    ids=['redirect_from_login', 'redirect_from_register', 'redirect_from_dashboard']
)
def test_is_referred_by_login_or_register(mock_is_testing_environment, path, expected_value):
    mock_is_testing_environment.return_value = False

    request = RequestFactory().request()
    request.META['HTTP_REFERER'] = f'http://example.com/{path}'
    flag = is_referred_by_login_or_register(request)

    assert flag is expected_value

"""
Tests for helpers of branding_extension app
"""
from freezegun import freeze_time

from openedx.adg.lms.branding_extension.helpers import get_copyright, get_footer_navigation_links


def test_get_footer_navigation_links(mocker):
    """
    Tests `get_footer_navigation_links` helper method of branding extension
    """
    test_url = 'test_url'
    test_support_url = 'test_support_url'
    mocker.patch('openedx.adg.lms.branding_extension.helpers.marketing_link', return_value=test_url)
    mocker.patch('openedx.adg.lms.branding_extension.helpers._build_support_form_url', return_value=test_support_url)

    branding_links = get_footer_navigation_links()
    assert len(branding_links) == 4
    assert branding_links == [
        {
            'url': test_url,
            'title': 'About',
        },
        {
            'url': test_url,
            'title': 'Our Team',
        },
        {
            'url': test_url,
            'title': 'Terms',
        },
        {
            'url': test_support_url,
            'title': 'Contact',
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

    assert get_copyright() == '\u00A9 {} {}.'.format(2021, test_platform_name)

"""
Context dictionary for templates that use the ace_common base template.
"""

from django.conf import settings
from django.urls import NoReverseMatch, reverse

from edxmako.shortcuts import marketing_link
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import get_config_value_from_site_or_settings
from openedx.features.edly.context_processor import get_theme_colors

DEFAULT_COLOR_DICT = {
    'primary': '#3E99D4',
    'secondary': '#1197EA'
}
DEFAULT_FONTS_DICT = {
    'base-font': "'Open Sans', sans-serif",
    'heading-font': "'Open Sans', sans-serif",
    'font-path': "<link href='https://fonts.googleapis.com/css?family=Open+Sans:400,600,700&display=swap' rel='stylesheet' />",
}
DEFAULT_BRANDING_DICT = {
    'logo': "https://edly-edx-theme-files.s3.amazonaws.com/st-lutherx-logo.png",
    'favicon': "https://edly-edx-theme-files.s3.amazonaws.com/favicon.ico",
}


def get_base_template_context(site):
    """
    Dict with entries needed for all templates that use the base template.
    """
    # When on LMS and a dashboard is available, use that as the dashboard url.
    # Otherwise, use the home url instead.
    try:
        dashboard_url = reverse('dashboard')
    except NoReverseMatch:
        dashboard_url = reverse('home')

    contact_mailing_address = configuration_helpers.get_value('CONTACT_MAILING_ADDRESS')

    if not contact_mailing_address:
        contact_mailing_address = get_config_value_from_site_or_settings(
            'CONTACT_MAILING_ADDRESS',
            site=site,
            site_config_name='CONTACT_MAILING_ADDRESS'
        )

    return {
        # Platform information
        'homepage_url': marketing_link('ROOT'),
        'dashboard_url': dashboard_url,
        'template_revision': getattr(settings, 'EDX_PLATFORM_REVISION', None),
        'platform_name': get_config_value_from_site_or_settings(
            'PLATFORM_NAME',
            site=site,
            site_config_name='platform_name',
        ),
        'contact_email': get_config_value_from_site_or_settings(
            'CONTACT_EMAIL', site=site, site_config_name='contact_email'),
        'contact_mailing_address': contact_mailing_address,
        'social_media_urls': get_config_value_from_site_or_settings('SOCIAL_MEDIA_FOOTER_URLS', site=site),
        'mobile_store_urls': get_config_value_from_site_or_settings('MOBILE_STORE_URLS', site=site),

        # Context processor values for dynamic theming
        'edly_colors_config': get_theme_colors(),
        'edly_fonts_config': configuration_helpers.get_dict('FONTS', DEFAULT_FONTS_DICT),
        'edly_branding_config': configuration_helpers.get_dict('BRANDING', DEFAULT_BRANDING_DICT),
        # Context processor value for edly app
        'edly_copyright_text': configuration_helpers.get_value('EDLY_COPYRIGHT_TEXT')
    }

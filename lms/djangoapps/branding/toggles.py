"""
Configuration for features of Branding
"""
from django.conf import settings

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def use_catalog_mfe():
    """
    Returns a boolean = true if the Catalog MFE is enabled.
    """
    return configuration_helpers.get_value(
        'ENABLE_CATALOG_MICROFRONTEND', settings.FEATURES.get('ENABLE_CATALOG_MICROFRONTEND')
    )

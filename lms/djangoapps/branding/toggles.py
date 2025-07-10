"""
Configuration for features of Branding
"""
from django.conf import settings

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def use_catalog_mfe():
    """
    Determine if Catalog MFE is enabled, replacing student_dashboard
    """
    return configuration_helpers.get_value(
        'ENABLE_CATALOG_MICROFRONTEND', settings.FEATURES['ENABLE_CATALOG_MICROFRONTEND']
    )

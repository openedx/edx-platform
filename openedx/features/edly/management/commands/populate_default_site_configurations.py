"""
Edly's management command to populate default site configuration for sites with empty site configuration.
"""

import logging

from django.core.management.base import BaseCommand
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

logger = logging.getLogger(__name__)

DEFAULT_SITE_CONFIGURATION = {
    "COLORS": {
        "primary": "#3E99D4",
        "secondary": "#3E99D4"
    },
    "FONTS": {
        "base-font": "Open Sans, sans-serif",
        "heading-font": "Open Sans, sans-serif",
        "font-path": "https://fonts.googleapis.com/css?family=Open+Sans&display=swap"
    },
    "BRANDING": {
        "logo": "https://edly-cloud-static-assets.s3.amazonaws.com/default-branding/logo.png",
        "logo-white": "https://edly-cloud-static-assets.s3.amazonaws.com/default-branding/logo-white.png",
        "favicon": "https://edly-cloud-static-assets.s3.amazonaws.com/default-branding/favicon.ico"
    }
}


class Command(BaseCommand):
    """
    Populate default site configuration for sites with empty site configuration.
    """
    help = "Populate Default Site Configuration for Sites with Empty Site Configuration."

    def handle(self, *args, **options):
        for site_configuration in SiteConfiguration.objects.all():
            if not site_configuration.site_values:
                site_configuration.site_values = DEFAULT_SITE_CONFIGURATION
                site_configuration.save()

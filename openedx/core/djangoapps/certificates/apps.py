"""
Openedx Certificates Application Configuration
"""

from django.apps import AppConfig


class OpenedxCertificatesConfig(AppConfig):
    """
    Application Configuration for Openedx Certificates.
    """
    name = 'openedx.core.djangoapps.certificates'
    label = 'openedx_certificates'

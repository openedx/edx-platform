"""
Certificates Application Configuration

Signal handlers are connected here.
"""


from django.apps import AppConfig
from django.conf import settings
from edx_proctoring.runtime import set_runtime_service


class CertificatesConfig(AppConfig):
    """
    Application Configuration for Certificates.
    """
    name = u'lms.djangoapps.certificates'

    def ready(self):
        """
        Connect handlers to signals.
        """
        # Can't import models at module level in AppConfigs, and models get
        # included from the signal handlers
        from . import signals  # pylint: disable=unused-import
        if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS'):
            from .services import CertificateService
            set_runtime_service('certificates', CertificateService())

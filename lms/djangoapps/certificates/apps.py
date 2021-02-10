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
        if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS'):
            from lms.djangoapps.certificates.services import CertificateService
            set_runtime_service('certificates', CertificateService())

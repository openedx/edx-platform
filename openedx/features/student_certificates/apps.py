from django.apps import AppConfig


class StudentCertificatesConfig(AppConfig):
    name = u'openedx.features.student_certificates'

    def ready(self):
        """
        Connect signal handlers.
        """
        import openedx.features.student_certificates.handlers

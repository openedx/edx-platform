"""
Defines the app name and connects the signal handlers associated with the student_certificates application.
"""
from django.apps import AppConfig


class StudentCertificatesConfig(AppConfig):
    name = u'openedx.features.student_certificates'

    def ready(self):
        """
        Connect signal handlers.
        """
        import openedx.features.student_certificates.handlers  # pylint: disable=unused-variable

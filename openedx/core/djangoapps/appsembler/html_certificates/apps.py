from django.apps import AppConfig


class HtmlCertificatesAppConfig(AppConfig):

    name = 'openedx.core.djangoapps.appsembler.html_certificates'
    label = 'html_certificates'

    def ready(self):
        from openedx.core.djangoapps.appsembler.html_certificates import signals  # pylint: disable=unused-variable

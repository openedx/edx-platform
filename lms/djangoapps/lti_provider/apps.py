"""
Configuration for the lti_provider Django application.
"""


from django.apps import AppConfig


class LtiProviderConfig(AppConfig):
    """
    Configuration class for the lti_provider Django application.
    """
    name = 'lms.djangoapps.lti_provider'
    verbose_name = "LTI Provider"

    def ready(self):
        pass

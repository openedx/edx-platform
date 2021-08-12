"""
Name Affirmation API App Configuration
"""


from django.apps import AppConfig
from django.conf import settings
from edx_proctoring.runtime import set_runtime_service


class NameAffirmationApiConfig(AppConfig):
    """
    Application Configuration for Misc Services.
    """
    name = 'openedx.features.name_affirmation_api'

    def ready(self):
        """
        Connect services.
        """
        if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS'):
            from edx_name_affirmation.services import NameAffirmationService
            set_runtime_service('name_affirmation', NameAffirmationService())

from django.apps import AppConfig
from django.contrib.auth.models import User
from student.models import UserProfile
from simple_history import register


class OnboardingConfig(AppConfig):
    name = u'onboarding'

    def ready(self):
        """
        Connect signal handlers.
        """
        import onboarding.handlers

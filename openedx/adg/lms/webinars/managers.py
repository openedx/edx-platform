"""
Webinar model managers
"""
from django.db import models
from django.db.models import Q


class WebinarRegistrationManager(models.Manager):
    """
    Manager for WebinarRegistration model
    """

    def webinar_team_and_active_user_registrations(self):
        """
        Get all registrations in which user is registered or is a registration of webinar team member.
        """
        return self.get_queryset().filter(
            Q(is_registered=True) | Q(is_team_member_registration=True)
        )

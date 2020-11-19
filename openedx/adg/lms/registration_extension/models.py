"""
Custom registration app models.
"""
from django.contrib.auth.models import User
from django.db import models

from openedx.adg.lms.registration_extension.constants import BUSINESS_LINES


class ExtendedUserProfile(models.Model):
    """
    Model to store user profile data for adg
    """

    user = models.OneToOneField(
        User, unique=True, db_index=True, related_name='extended_profile', on_delete=models.CASCADE)
    company = models.CharField(blank=True, null=True, max_length=50, choices=BUSINESS_LINES)

    class Meta:
        app_label = 'registration_extension'

"""
Custom registration app models.
"""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from openedx.adg.lms.applications.models import BusinessLine


class ExtendedUserProfile(models.Model):
    """
    Model to store user profile data for adg
    """

    user = models.OneToOneField(
        User, unique=True, db_index=True, related_name='extended_profile', on_delete=models.CASCADE)

    birth_date = models.DateField(verbose_name=_('Birth Date'), null=True)
    saudi_national = models.BooleanField(verbose_name=_('Saudi National'), null=True)

    company = models.OneToOneField(BusinessLine, on_delete=models.CASCADE, null=True)

    class Meta:
        app_label = 'registration_extension'

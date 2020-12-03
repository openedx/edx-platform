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
        User, db_index=True, related_name='extended_profile', on_delete=models.CASCADE)

    birth_date = models.DateField(verbose_name=_('Birth Date'), null=True, )
    saudi_national = models.BooleanField(verbose_name=_('Saudi National'), null=True, )

    company = models.ForeignKey(BusinessLine, verbose_name=_('Company'),
                                on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        app_label = 'registration_extension'

"""
Custom registration app models.
"""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from openedx.adg.lms.applications.models import BusinessLine
from openedx.adg.lms.constants import SAUDI_NATIONAL_PROMPT


class ExtendedUserProfile(models.Model):
    """
    Model to store user profile data for adg
    """

    user = models.OneToOneField(User, db_index=True, related_name='extended_profile', on_delete=models.CASCADE)
    birth_date = models.DateField(verbose_name=_('Birth Date'), null=True, )
    saudi_national = models.BooleanField(verbose_name=SAUDI_NATIONAL_PROMPT, null=True, )
    company = models.ForeignKey(
        BusinessLine, verbose_name=_('Company'), on_delete=models.CASCADE, null=True, blank=True
    )
    hear_about_omni = models.CharField(
        verbose_name=_('How did you hear about this program?'),
        max_length=255,
        blank=True,
    )

    @property
    def is_saudi_national(self):
        if self.saudi_national:
            return _('Yes')
        return _('No')

    @property
    def is_saudi_national_and_has_birthdate(self):
        """
        Checks if a user is a saudi national and has the birthdate field added
        """
        return self.saudi_national and self.birth_date is not None

    class Meta:
        app_label = 'registration_extension'

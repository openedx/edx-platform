from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from model_utils.models import TimeStampedModel


class Partner(TimeStampedModel):
    """
    This model represents white-labelled partners.
    """
    performance_url = models.URLField(blank=True, default=None)
    label = models.CharField(max_length=100, help_text="Display as a Title in Landing page.")
    logo = models.ImageField(upload_to="partners/logo", help_text="Main Logo in Landing page.")
    slug = models.CharField(max_length=100, unique=True, help_text="A Unique Identifier for an Organization")
    email = models.EmailField(help_text="Contact Email of an Organization")

    def __unicode__(self):
        return '{}'.format(self.label)

    class Meta:
        verbose_name = "Partner"
        verbose_name_plural = "Partners"


class PartnerUser(TimeStampedModel):
    """
    This model represents all the users that are associated to a partner.
    """
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE, related_name="partner_user")
    partner = models.ForeignKey(Partner, db_index=True, on_delete=models.CASCADE, related_name="partner")

    def __unicode__(self):
        return '{partner}-{user}'.format(partner=self.partner.label, user=self.user.username)

    class Meta:
        unique_together = ('user', 'partner')


class PartnerCommunity(models.Model):
    community_id = models.IntegerField()
    partner = models.ForeignKey(Partner, db_index=True, on_delete=models.CASCADE, related_name='communities')

    class Meta:
        unique_together = ('community_id', 'partner')


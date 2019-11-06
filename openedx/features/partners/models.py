from django.contrib.auth.models import User
from django.db import models
from model_utils.models import TimeStampedModel


class Partner(TimeStampedModel):
    """
    This model represents white-labelled partners.
    """
    label = models.CharField(max_length=100, default=None, null=False)
    main_logo = models.CharField(max_length=255, default=None, null=True)
    small_logo = models.CharField(max_length=255, default=None, null=True)
    slug = models.CharField(max_length=100, default=None, null=False, unique=True)

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
        return '{}'.format(self.partner.name)

    class Meta:
        unique_together = ('user', 'partner')


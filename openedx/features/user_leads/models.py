from django.contrib.auth.models import User
from django.db import models

from .constants import UTM_DEFAULT_ORIGIN


class UserLeads(models.Model):
    """
    These leads represents the utm information to track a source,
    medium, and campaign name. This enables Google Analytics to tell
    you where searchers came from as well as what campaign directed them to you.

    This model was updated to include a custom `origin` field, to store
    the page a user was on when a certain lead was stored making this
    a platform-wide generic model for leads, as per requirements.
    """
    user = models.ForeignKey(User, db_index=True)
    utm_source = models.CharField(max_length=255, default=None, null=True)
    utm_medium = models.CharField(max_length=255, default=None, null=True)
    utm_campaign = models.CharField(max_length=255, default=None, null=True)
    utm_content = models.CharField(max_length=255, default=None, null=True)
    utm_term = models.CharField(max_length=255, default=None, null=True)
    date_created = models.DateTimeField(auto_now=True)
    origin = models.CharField(max_length=255, default=UTM_DEFAULT_ORIGIN)

    def __unicode__(self):
        return '{}'.format(self.user.username)

    class Meta:
        unique_together = ('user', 'origin', )
        verbose_name = "User Lead"
        verbose_name_plural = "User Leads"

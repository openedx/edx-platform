from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.utils.translation import ugettext_lazy as _


class Organization(TimeStampedModel):
    """
    Represents the organization the user belongs to.  AMC admins can add
    users to their organization; Courses displayed on edX must be filtered
    by organization.
    Studio hosts the source of truth for this data.  A minimal subset of that
    data is replicated here to allow us to attach users to organizations.
    """

    key = models.CharField(
        help_text=_('The string value of an org key identifying this organization in the LMS.'),
        unique=True,
        max_length=64,
        db_index=True,
    )
    display_name = models.CharField(
        help_text=_('The display name of this organization.'),
        unique=True,
        max_length=128,
    )

    def __unicode__(self):
        return unicode(self.display_name)
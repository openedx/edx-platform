"""Models for API management."""
import logging

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
from django_extensions.db.models import TimeStampedModel
from simple_history.models import HistoricalRecords


log = logging.getLogger(__name__)


class ApiAccessRequest(TimeStampedModel):
    """Model to track API access for a user."""

    PENDING = 'pending'
    DENIED = 'denied'
    APPROVED = 'approved'
    STATUS_CHOICES = (
        (PENDING, _('Pending')),
        (DENIED, _('Denied')),
        (APPROVED, _('Approved')),
    )
    user = models.ForeignKey(User)
    status = models.CharField(
        max_length=255,
        choices=STATUS_CHOICES,
        default=PENDING,
        db_index=True,
        help_text=_('Status of this API access request'),
    )
    website = models.URLField(help_text=_('The URL of the website associated with this API user.'))
    reason = models.TextField(help_text=_('The reason this user wants to access the API.'))

    history = HistoricalRecords()

    @classmethod
    def has_api_access(cls, user):
        """Returns whether or not this user has been granted API access.

        Arguments:
            user (User): The user to check access for.

        Returns:
            bool
        """
        return cls.objects.filter(user=user, status=cls.APPROVED).exists()

    def approve(self):
        """Approve this request."""
        log.info('Approving API request from user [%s].', self.user.id)
        self.status = self.APPROVED
        self.save()

    def deny(self):
        """Deny this request."""
        log.info('Denying API request from user [%s].', self.user.id)
        self.status = self.DENIED
        self.save()

    def __unicode__(self):
        return u'ApiAccessRequest {website} [{status}]'.format(website=self.website, status=self.status)

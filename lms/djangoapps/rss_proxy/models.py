"""
Models for the rss_proxy djangoapp.
"""
from __future__ import absolute_import

import six
from django.db import models
from model_utils.models import TimeStampedModel


class WhitelistedRssUrl(TimeStampedModel):
    """
    Model for persisting RSS feed URLs which are whitelisted
    for proxying via this rss_proxy djangoapp.

    .. no_pii:
    """
    url = models.CharField(max_length=255, unique=True, db_index=True)

    class Meta(object):
        """ Meta class for this Django model """
        app_label = "rss_proxy"

    def __unicode__(self):
        return six.text_type(self.url)

"""
Models for the rss_proxy djangoapp.
"""


import six
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from model_utils.models import TimeStampedModel


@python_2_unicode_compatible
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

    def __str__(self):
        return six.text_type(self.url)

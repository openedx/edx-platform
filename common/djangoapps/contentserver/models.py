"""
Models for contentserver
"""

from django.db.models.fields import PositiveIntegerField
from config_models.models import ConfigurationModel


class CourseAssetCacheTtlConfig(ConfigurationModel):
    """Configuration for the TTL of course assets."""

    class Meta(object):
        app_label = 'contentserver'

    cache_ttl = PositiveIntegerField(
        default=0,
        help_text="The time, in seconds, to report that a course asset is allowed to be cached for."
    )

    @classmethod
    def get_cache_ttl(cls):
        """Gets the cache TTL for course assets, if present"""
        return cls.current().cache_ttl

    def __repr__(self):
        return '<CourseAssetCacheTtlConfig(cache_ttl={})>'.format(self.get_cache_ttl())

    def __unicode__(self):
        return unicode(repr(self))

"""
Models for contentserver
"""

from django.db.models.fields import PositiveIntegerField, TextField
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


class CdnUserAgentsConfig(ConfigurationModel):
    """Configuration for the user agents we expect to see from CDNs."""

    class Meta(object):
        app_label = 'contentserver'

    cdn_user_agents = TextField(
        default='Amazon CloudFront',
        help_text="A newline-separated list of user agents that should be considered CDNs."
    )

    @classmethod
    def get_cdn_user_agents(cls):
        """Gets the list of CDN user agents, if present"""
        return cls.current().cdn_user_agents

    def __repr__(self):
        return '<WhitelistedCdnConfig(cdn_user_agents={})>'.format(self.get_cdn_user_agents())

    def __unicode__(self):
        return unicode(repr(self))

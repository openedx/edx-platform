"""
Models for contentserver
"""
from config_models.models import ConfigurationModel
from django.db.models.fields import PositiveIntegerField, TextField


class CourseAssetCacheTtlConfig(ConfigurationModel):
    """
    Configuration for the TTL of course assets.

    .. no_pii:
    """

    class Meta:
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
        return f'<CourseAssetCacheTtlConfig(cache_ttl={self.get_cache_ttl()})>'

    def __str__(self):
        return str(repr(self))


class CdnUserAgentsConfig(ConfigurationModel):
    """
    Configuration for the user agents we expect to see from CDNs.

    .. no_pii:
    """

    class Meta:
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
        return f'<WhitelistedCdnConfig(cdn_user_agents={self.get_cdn_user_agents()})>'

    def __str__(self):
        return str(repr(self))

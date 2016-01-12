"""
Models for static_replace
"""

from django.db.models.fields import TextField
from config_models.models import ConfigurationModel


class AssetBaseUrlConfig(ConfigurationModel):
    """Configuration for the base URL used for static assets."""

    class Meta(object):
        app_label = 'static_replace'

    base_url = TextField(
        blank=True,
        help_text="The alternative hostname to serve static assets from.  Should be in the form of hostname[:port]."
    )

    @classmethod
    def get_base_url(cls):
        """Gets the base URL to use for serving static assets, if present"""
        return cls.current().base_url

    def __repr__(self):
        return '<AssetBaseUrlConfig(base_url={})>'.format(self.get_base_url())

    def __unicode__(self):
        return unicode(repr(self))

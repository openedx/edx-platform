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


class AssetExcludedExtensionsConfig(ConfigurationModel):
    """Configuration for the the excluded file extensions when canonicalizing static asset paths."""

    class Meta(object):
        app_label = 'static_replace'

    excluded_extensions = TextField(
        default='html',
        help_text='The file extensions to exclude from canonicalization.  No leading period required. ' +
        'Values should be space separated i.e. "html svg css"'
    )

    @classmethod
    def get_excluded_extensions(cls):
        """Gets the excluded file extensions when canonicalizing static asset paths"""
        add_period = lambda x: '.' + x
        return map(add_period, cls.current().excluded_extensions.split())

    def __repr__(self):
        return '<AssetExcludedExtensionsConfig(extensions={})>'.format(self.get_excluded_extensions())

    def __unicode__(self):
        return unicode(repr(self))

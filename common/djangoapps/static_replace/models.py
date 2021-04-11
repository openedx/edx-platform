"""
Models for static_replace
"""


import six
from six.moves import map

from config_models.models import ConfigurationModel
from django.db.models.fields import TextField
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class AssetBaseUrlConfig(ConfigurationModel):
    """
    Configuration for the base URL used for static assets.

    .. no_pii:
    """

    class Meta(object):
        app_label = 'static_replace'

    base_url = TextField(
        blank=True,
        help_text=u"The alternative hostname to serve static assets from.  Should be in the form of hostname[:port]."
    )

    @classmethod
    def get_base_url(cls):
        """Gets the base URL to use for serving static assets, if present"""
        return cls.current().base_url

    def __repr__(self):
        return '<AssetBaseUrlConfig(base_url={})>'.format(self.get_base_url())

    def __str__(self):
        return six.text_type(repr(self))


@python_2_unicode_compatible
class AssetExcludedExtensionsConfig(ConfigurationModel):
    """
    Configuration for the the excluded file extensions when canonicalizing static asset paths.

    .. no_pii:
    """

    class Meta(object):
        app_label = 'static_replace'

    excluded_extensions = TextField(
        default=u'html',
        help_text=u'The file extensions to exclude from canonicalization.  No leading period required. ' +
        'Values should be space separated i.e. "html svg css"'
    )

    @classmethod
    def get_excluded_extensions(cls):
        """Gets the excluded file extensions when canonicalizing static asset paths"""
        add_period = lambda x: '.' + x
        return list(map(add_period, cls.current().excluded_extensions.split()))

    def __repr__(self):
        return '<AssetExcludedExtensionsConfig(extensions={})>'.format(self.get_excluded_extensions())

    def __str__(self):
        return six.text_type(repr(self))

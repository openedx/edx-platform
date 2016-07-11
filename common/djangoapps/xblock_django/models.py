"""
Models.
"""
from django.utils.translation import ugettext_lazy as _

from django.conf import settings

from django.db.models import TextField
from django.db import models

from config_models.models import ConfigurationModel


class XBlockDisableConfig(ConfigurationModel):
    """
    Configuration for disabling and deprecating XBlocks.
    """

    class Meta(ConfigurationModel.Meta):
        app_label = 'xblock_django'

    disabled_blocks = TextField(
        default='', blank=True,
        help_text=_('Space-separated list of XBlocks which should not render.')
    )

    disabled_create_blocks = TextField(
        default='', blank=True,
        help_text=_(
            "Space-separated list of XBlock types whose creation to disable in Studio."
        )
    )

    @classmethod
    def is_block_type_disabled(cls, block_type):
        """ Return True if block_type is disabled. """

        config = cls.current()
        if not config.enabled:
            return False

        return block_type in config.disabled_blocks.split()

    @classmethod
    def disabled_create_block_types(cls):
        """ Return list of deprecated XBlock types. Merges types in settings file and field. """

        config = cls.current()
        xblock_types = config.disabled_create_blocks.split() if config.enabled else []

        # Merge settings list with one in the admin config;
        if hasattr(settings, 'DEPRECATED_ADVANCED_COMPONENT_TYPES'):
            xblock_types.extend(
                xblock_type for xblock_type in settings.DEPRECATED_ADVANCED_COMPONENT_TYPES
                if xblock_type not in xblock_types
            )

        return xblock_types

    def __unicode__(self):
        config = XBlockDisableConfig.current()
        return u"Disabled xblocks = {disabled_xblocks}\nDeprecated xblocks = {disabled_create_block_types}".format(
            disabled_xblocks=config.disabled_blocks,
            disabled_create_block_types=config.disabled_create_block_types
        )


class XBlockConfiguration(ConfigurationModel):
    """
    XBlock configuration used by both LMS and Studio, and not specific to a particular template.
    """

    KEY_FIELDS = ('name',)  # xblock name is unique

    class Meta(ConfigurationModel.Meta):
        app_label = 'xblock_django'

    # boolean field 'enabled' inherited from parent ConfigurationModel
    name = models.CharField(max_length=255, null=False, db_index=True)
    deprecated = models.BooleanField(
        default=False,
        verbose_name=_('show deprecation messaging in Studio')
    )

    def __unicode__(self):
        return (
            "XBlockConfiguration(name={}, enabled={}, deprecated={})"
        ).format(self.name, self.enabled, self.deprecated)


class XBlockStudioConfigurationFlag(ConfigurationModel):
    """
    Enables site-wide Studio configuration for XBlocks.
    """

    class Meta(object):
        app_label = "xblock_django"

    # boolean field 'enabled' inherited from parent ConfigurationModel

    def __unicode__(self):
        return "XBlockStudioConfigurationFlag(enabled={})".format(self.enabled)


class XBlockStudioConfiguration(ConfigurationModel):
    """
    Studio editing configuration for a specific XBlock/template combination.
    """
    KEY_FIELDS = ('name', 'template')  # xblock name/template combination is unique

    FULL_SUPPORT = 'fs'
    PROVISIONAL_SUPPORT = 'ps'
    UNSUPPORTED = 'us'

    SUPPORT_CHOICES = (
        (FULL_SUPPORT, _('Fully Supported')),
        (PROVISIONAL_SUPPORT, _('Provisionally Supported')),
        (UNSUPPORTED, _('Unsupported'))
    )

    # boolean field 'enabled' inherited from parent ConfigurationModel
    name = models.CharField(max_length=255, null=False, db_index=True)
    template = models.CharField(max_length=255, blank=True, default='')
    support_level = models.CharField(max_length=2, choices=SUPPORT_CHOICES, default=UNSUPPORTED)

    class Meta(object):
        app_label = "xblock_django"

    def __unicode__(self):
        return (
            "XBlockStudioConfiguration(name={}, template={}, enabled={}, support_level={})"
        ).format(self.name, self.template, self.enabled, self.support_level)

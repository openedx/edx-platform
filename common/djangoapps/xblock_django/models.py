"""
Models.
"""
from django.utils.translation import ugettext_lazy as _

from django.conf import settings

from django.db.models import TextField

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
    def disabled_block_types(cls):
        """ Return list of disabled xblock types. """

        config = cls.current()
        if not config.enabled:
            return ()

        return config.disabled_blocks.split()

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

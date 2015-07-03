"""
Models.
"""
from django.utils.translation import ugettext_lazy as _

from django.db.models import TextField

from config_models.models import ConfigurationModel


class XBlockDisableConfig(ConfigurationModel):
    """
    Configuration for disabling XBlocks.
    """

    disabled_blocks = TextField(
        default='', blank=True,
        help_text=_('Space-separated list of XBlocks which should not render.')
    )

    @classmethod
    def is_block_type_disabled(cls, block_type):
        """ Return True if block_type is disabled. """

        config = cls.current()
        if not config.enabled:
            return False

        return block_type in config.disabled_blocks.split()  # pylint: disable=no-member

    @classmethod
    def disabled_block_types(cls):
        """ Return list of disabled xblock types. """

        config = cls.current()
        if not config.enabled:
            return ()

        return config.disabled_blocks.split()  # pylint: disable=no-member

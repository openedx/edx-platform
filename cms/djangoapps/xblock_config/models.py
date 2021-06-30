"""
Models used by Studio XBlock infrastructure.

Includes:
    StudioConfig: A ConfigurationModel for managing Studio.
"""
from config_models.models import ConfigurationModel
from django.db.models import TextField


class StudioConfig(ConfigurationModel):
    """
    Configuration for XBlockAsides.

    .. no_pii:
    """
    disabled_blocks = TextField(
        default="about course_info static_tab",
        help_text="Space-separated list of XBlocks on which XBlockAsides should never render in studio",
    )

    @classmethod
    def asides_enabled(cls, block_type):
        """
        Return True if asides are enabled for this type of block in studio
        """
        studio_config = cls.current()
        return studio_config.enabled and block_type not in studio_config.disabled_blocks.split()

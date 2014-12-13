"""
Models used by LMS XBlock infrastructure.

Includes:
    XBlockAsidesConfig: A ConfigurationModel for managing how XBlockAsides are
        rendered in the LMS.
"""

from django.db.models import TextField

from config_models.models import ConfigurationModel

from xblock.core import XBlockAside


class XBlockAsidesConfig(ConfigurationModel):
    """
    Configuration for XBlockAsides.
    """

    disabled_blocks = TextField(
        default="about course_info static_tab",
        help_text="Space-separated list of XBlocks on which XBlockAsides should never render."
    )

    @classmethod
    def possible_asides(cls):
        """
        Return a list of all asides that are enabled across all XBlocks.
        """
        return [aside_type for aside_type, __ in XBlockAside.load_classes()]

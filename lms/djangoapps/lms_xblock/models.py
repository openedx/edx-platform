from django.db.models import TextField

from config_models.models import ConfigurationModel

class XBlockAsidesConfig(ConfigurationModel):
    """
    Configuration for XBlockAsides.
    """

    disabled_blocks = TextField(
        default="about course_info static_tab",
        help_text="Space-separated list of XBlocks on which XBlockAsides should never render."
    )

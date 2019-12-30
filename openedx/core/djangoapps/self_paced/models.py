"""
Configuration for self-paced courses.
"""


from config_models.models import ConfigurationModel
from django.db.models import BooleanField
from django.utils.translation import ugettext_lazy as _


class SelfPacedConfiguration(ConfigurationModel):
    """
    Configuration for self-paced courses.

    .. no_pii:
    """

    enable_course_home_improvements = BooleanField(
        default=False,
        verbose_name=_("Enable course home page improvements.")
    )

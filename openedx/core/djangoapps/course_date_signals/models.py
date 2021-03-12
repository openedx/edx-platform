"""
Models for configuration course_date_signals

SelfPacedRelativeDatesConfig:
    manage which orgs/courses/course runs have self-paced relative dates enabled
"""

from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel


class SelfPacedRelativeDatesConfig(StackedConfigurationModel):
    """
    Configuration to manage the SelfPacedRelativeDates settings.

    .. no_pii:
    """

"""
Provides configuration models for Adaptive Learning
"""

from config_models.models import ConfigurationModel


class AdaptiveLearningEnabledFlag(ConfigurationModel):
    """
    A flag that enables/disables Adaptive Learning across an entire instance.
    """

    class Meta(object):
        app_label = "adaptive_learning"

    def __unicode__(self):
        return u"AdaptiveLearningEnabledFlag: enabled {}".format(self.enabled)

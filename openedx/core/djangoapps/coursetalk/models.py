"""
Models for CourseTalk configurations
"""
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from config_models.models import ConfigurationModel


class CourseTalkWidgetConfiguration(ConfigurationModel):
    """
    This model represents Enable Configuration for CourseTalk widget.
    If the setting enabled, widget will will be available on course
    info page and on course about page.
    """
    platform_key = models.fields.CharField(
        max_length=50,
        help_text=_(
            "The platform key associates CourseTalk widgets with your platform. "
            "Generally, it is the domain name for your platform. For example, "
            "if your platform is http://edx.org, the platform key is \"edx\"."
        )
    )

    @classmethod
    def get_platform_key(cls):
        """
        Return platform_key for current active configuration.
        If current configuration is not enabled - return empty string

        :return: Platform key
        :rtype: unicode
        """
        return cls.current().platform_key if cls.is_enabled() else ''

    def __unicode__(self):
        return 'CourseTalkWidgetConfiguration - {0}'.format(self.enabled)

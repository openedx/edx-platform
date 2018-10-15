# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from openedx.core.lib.config_model_utils import (
    CourseStackedConfigurationModel,
    GlobalStackedConfigurationModel,
    OrgStackedConfigurationModel,
    SiteStackedConfigurationModel,
    StackedConfigurationModel,
)


class CourseDurationLimitsConfig(models.Model):
    class Meta(object):
        abstract = True

    enabled_after = models.DateTimeField()
    STACKABLE_FIELDS = ['enabled', 'enabled_after']

    @classmethod
    def is_enabled(cls, enrollment):
        current_config = CourseCourseDurationLimitsConfig.stacked_current(
            CourseOverview.objects.get(id=enrollment.course_id)
        )

        return current_config.enabled and current_config.enabled_after <= enrollment.created



class GlobalCourseDurationLimitsConfig(CourseDurationLimitsConfig, GlobalStackedConfigurationModel):
    pass


class SiteCourseDurationLimitsConfig(CourseDurationLimitsConfig, SiteStackedConfigurationModel):
    pass


class OrgCourseDurationLimitsConfig(CourseDurationLimitsConfig, OrgStackedConfigurationModel):
    pass


class CourseCourseDurationLimitsConfig(CourseDurationLimitsConfig, CourseStackedConfigurationModel):
    pass

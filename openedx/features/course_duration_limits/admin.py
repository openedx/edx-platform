# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin
from openedx.features.course_duration_limits.models import (
    GlobalCourseDurationLimitsConfig,
    SiteCourseDurationLimitsConfig,
    OrgCourseDurationLimitsConfig,
    CourseCourseDurationLimitsConfig,
)


# Register your models here.
class GlobalCourseDurationLimitsConfigAdmin(ConfigurationModelAdmin):
    pass

class SiteCourseDurationLimitsConfigAdmin(KeyedConfigurationModelAdmin):
    pass

class OrgCourseDurationLimitsConfigAdmin(KeyedConfigurationModelAdmin):
    pass

class CourseCourseDurationLimitsConfigAdmin(KeyedConfigurationModelAdmin):
    pass


admin.site.register(GlobalCourseDurationLimitsConfig, GlobalCourseDurationLimitsConfigAdmin)
admin.site.register(SiteCourseDurationLimitsConfig, SiteCourseDurationLimitsConfigAdmin)
admin.site.register(OrgCourseDurationLimitsConfig, OrgCourseDurationLimitsConfigAdmin)
admin.site.register(CourseCourseDurationLimitsConfig, CourseCourseDurationLimitsConfigAdmin)

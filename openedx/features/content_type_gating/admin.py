# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin
from openedx.features.content_type_gating.models import (
    GlobalContentTypeGatingConfig,
    SiteContentTypeGatingConfig,
    OrgContentTypeGatingConfig,
    CourseContentTypeGatingConfig,
)


# Register your models here.
class GlobalContentTypeGatingConfigAdmin(ConfigurationModelAdmin):
    pass

class SiteContentTypeGatingConfigAdmin(KeyedConfigurationModelAdmin):
    pass

class OrgContentTypeGatingConfigAdmin(KeyedConfigurationModelAdmin):
    pass

class CourseContentTypeGatingConfigAdmin(KeyedConfigurationModelAdmin):
    pass


admin.site.register(GlobalContentTypeGatingConfig, GlobalContentTypeGatingConfigAdmin)
admin.site.register(SiteContentTypeGatingConfig, SiteContentTypeGatingConfigAdmin)
admin.site.register(OrgContentTypeGatingConfig, OrgContentTypeGatingConfigAdmin)
admin.site.register(CourseContentTypeGatingConfig, CourseContentTypeGatingConfigAdmin)

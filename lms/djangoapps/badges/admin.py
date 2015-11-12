"""
Admin registration for Badge Models
"""
from django.contrib import admin
from badges.models import CourseCompleteImageConfiguration, CourseEventBadgesConfiguration, BadgeClass
from config_models.admin import ConfigurationModelAdmin

admin.site.register(CourseCompleteImageConfiguration)
admin.site.register(BadgeClass)
admin.site.register(CourseEventBadgesConfiguration, ConfigurationModelAdmin)

"""
Django admin dashboard configuration for LMS XBlock infrastructure.
"""


from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin
from django.contrib import admin

from cms.djangoapps.xblock_config.forms import CourseEditLTIFieldsEnabledAdminForm
from cms.djangoapps.xblock_config.models import CourseEditLTIFieldsEnabledFlag, StudioConfig


class CourseEditLTIFieldsEnabledFlagAdmin(KeyedConfigurationModelAdmin):
    """
    Admin for LTI Fields Editing feature on course-by-course basis.
    Allows searching by course id.
    """
    form = CourseEditLTIFieldsEnabledAdminForm
    search_fields = ['course_id']
    fieldsets = (
        (None, {
            'fields': ('course_id', 'enabled'),
            'description': 'Enter a valid course id. If it is invalid, an error message will be displayed.'
        }),
    )

admin.site.register(StudioConfig, ConfigurationModelAdmin)
admin.site.register(CourseEditLTIFieldsEnabledFlag, CourseEditLTIFieldsEnabledFlagAdmin)

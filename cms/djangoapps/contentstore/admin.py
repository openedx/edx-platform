"""
Admin site bindings for contentstore
"""

from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin
from django.contrib import admin

from contentstore.config.forms import CourseNewAssetsPageAdminForm
from contentstore.config.models import CourseNewAssetsPageFlag, NewAssetsPageFlag
from contentstore.models import PushNotificationConfig, VideoUploadConfig


class CourseNewAssetsPageAdmin(KeyedConfigurationModelAdmin):
    """
    Admin for enabling new asset page on a course-by-course basis.
    Allows searching by course id.
    """
    form = CourseNewAssetsPageAdminForm
    search_fields = ['course_id']
    fieldsets = (
        (None, {
            'fields': ('course_id', 'enabled'),
            'description': 'Enter a valid course id. If it is invalid, an error message will display.'
        }),
    )

admin.site.register(NewAssetsPageFlag, ConfigurationModelAdmin)
admin.site.register(CourseNewAssetsPageFlag, CourseNewAssetsPageAdmin)

admin.site.register(VideoUploadConfig, ConfigurationModelAdmin)
admin.site.register(PushNotificationConfig, ConfigurationModelAdmin)

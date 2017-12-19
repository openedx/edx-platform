"""
Django admin for Video Pipeline models.
"""
from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from openedx.core.djangoapps.video_config.admin import CourseSpecificEnabledFlagBaseAdmin
from openedx.core.djangoapps.video_pipeline.forms import CourseVideoUploadsEnabledByDefaultAdminForm
from openedx.core.djangoapps.video_pipeline.models import (
    VideoPipelineIntegration,
    VideoUploadsEnabledByDefault,
    CourseVideoUploadsEnabledByDefault,
)


class CourseVideoUploadsEnabledByDefaultAdmin(CourseSpecificEnabledFlagBaseAdmin):
    """
    Admin of video uploads enabled by default feature on course-by-course basis.
    Allows searching by course id.
    """
    form = CourseVideoUploadsEnabledByDefaultAdminForm

admin.site.register(VideoPipelineIntegration, ConfigurationModelAdmin)

admin.site.register(VideoUploadsEnabledByDefault, ConfigurationModelAdmin)
admin.site.register(CourseVideoUploadsEnabledByDefault, CourseVideoUploadsEnabledByDefaultAdmin)

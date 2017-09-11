"""
Django admin dashboard configuration for Video XModule.
"""

from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin
from django.contrib import admin

from openedx.core.djangoapps.video_config.forms import (
    CourseHLSPlaybackFlagAdminForm, CourseVideoTranscriptFlagAdminForm
)
from openedx.core.djangoapps.video_config.models import (
    CourseHLSPlaybackEnabledFlag, HLSPlaybackEnabledFlag,
    CourseVideoTranscriptEnabledFlag, VideoTranscriptEnabledFlag
)


class CourseSpecificEnabledFlagBaseAdmin(KeyedConfigurationModelAdmin):
    """
    Admin of course specific feature on course-by-course basis.
    Allows searching by course id.
    """
    # Make abstract base class
    class Meta(object):
        abstract = True

    search_fields = ['course_id']
    fieldsets = (
        (None, {
            'fields': ('course_id', 'enabled'),
            'description': 'Enter a valid course id. If it is invalid, an error message will be displayed.'
        }),
    )


class CourseHLSPlaybackEnabledFlagAdmin(CourseSpecificEnabledFlagBaseAdmin):
    """
    Admin of HLS Playback feature on course-by-course basis.
    Allows searching by course id.
    """
    form = CourseHLSPlaybackFlagAdminForm


class CourseVideoTranscriptEnabledFlagAdmin(CourseSpecificEnabledFlagBaseAdmin):
    """
    Admin of Video Transcript feature on course-by-course basis.
    Allows searching by course id.
    """
    form = CourseHLSPlaybackFlagAdminForm

admin.site.register(HLSPlaybackEnabledFlag, ConfigurationModelAdmin)
admin.site.register(CourseHLSPlaybackEnabledFlag, CourseHLSPlaybackEnabledFlagAdmin)
admin.site.register(VideoTranscriptEnabledFlag, ConfigurationModelAdmin)
admin.site.register(CourseVideoTranscriptEnabledFlag, CourseHLSPlaybackEnabledFlagAdmin)

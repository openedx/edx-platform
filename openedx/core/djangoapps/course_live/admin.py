"""
Admin interface for course live configuration
"""
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from openedx.core.djangoapps.course_live.models import CourseLiveConfiguration


class CourseLiveConfigurationAdmin(SimpleHistoryAdmin):
    """
    Admin interface for the course live configuration
    """
    search_fields = (
        'course_key',
        'enabled',
        'provider_type',
    )
    list_filter = (
        'enabled',
        'provider_type',
    )


admin.site.register(CourseLiveConfiguration, CourseLiveConfigurationAdmin)

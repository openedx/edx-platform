"""
Admin for Adaptive Learning
"""
from django.contrib import admin

from config_models.admin import (
    ConfigurationModelAdmin,
    KeyedConfigurationModelAdmin
)

from adaptive_learning.config.forms import CourseAdaptiveLearningFlagForm
from adaptive_learning.config.models import (
    AdaptiveLearningEnabledFlag,
    CourseAdaptiveLearningFlag
)


class CourseAdaptiveLearningFlagAdmin(KeyedConfigurationModelAdmin):
    """
    Admin for enabling Adaptive Learning feature for a course.
    Allows searching by course id.
    """
    form = CourseAdaptiveLearningFlagForm
    search_fields = ['course_id']
    fieldsets = (
        (None, {
            'fields': ('course_id', 'enabled'),
            'description': 'Enter a valid course id. If it is invalid, an error message will display.'
        }),
    )

admin.site.register(AdaptiveLearningEnabledFlag, ConfigurationModelAdmin)
admin.site.register(CourseAdaptiveLearningFlag, CourseAdaptiveLearningFlagAdmin)

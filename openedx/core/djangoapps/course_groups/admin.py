"""
Provides Django admin interface for CourseCohortsSettings. Useful for when only the CMS is
used and the normal LMS interface is unavailable.
"""
from django.contrib import admin
from .models import CourseCohortsSettings


class CourseCohortsSettingsAdmin(admin.ModelAdmin):
    """
    Provides editing interface for the CourseCohortsSettings model.
    """
    list_display = ('course_id',)


admin.site.register(CourseCohortsSettings, CourseCohortsSettingsAdmin)

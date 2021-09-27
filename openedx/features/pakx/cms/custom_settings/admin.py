"""
Admin configuration for custom settings app models
"""
from django.contrib import admin

from .models import CourseOverviewContent, CourseSet


class CourseOverviewContentAdmin(admin.ModelAdmin):
    """
    Admin interface for the CourseOverviewContent object.
    """

    class Meta(object):
        """
        Meta class for CourseOverviewContent admin model
        """
        model = CourseOverviewContent


@admin.register(CourseSet)
class CourseSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'publisher_org', 'description', 'logo_url', 'video_url']


admin.site.register(CourseOverviewContent, CourseOverviewContentAdmin)

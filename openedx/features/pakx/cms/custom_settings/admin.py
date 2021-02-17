"""
Admin configuration for custom settings app models
"""
from django.contrib import admin

from .models import CourseOverviewContent


class CourseOverviewContentAdmin(admin.ModelAdmin):
    """
    Admin interface for the CourseOverviewContent object.
    """

    class Meta(object):
        """
        Meta class for CourseOverviewContent admin model
        """
        model = CourseOverviewContent


admin.site.register(CourseOverviewContent, CourseOverviewContentAdmin)

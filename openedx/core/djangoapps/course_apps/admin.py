"""
Django Admin pages for course_apps.
"""

from django.contrib import admin

from .models import CourseAppStatus


class CourseAppStatusAdmin(admin.ModelAdmin):
    """Admin for CourseAppStatus"""
    search_fields = ('course_key', )
    list_display = ('course_key', 'app_id', 'enabled')


admin.site.register(CourseAppStatus, CourseAppStatusAdmin)

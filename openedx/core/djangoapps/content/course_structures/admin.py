"""
Django Admin model registry for Course Structures sub-application
"""
from ratelimitbackend import admin

from .models import CourseStructure


class CourseStructureAdmin(admin.ModelAdmin):
    """
    Django Admin class for managing Course Structures model data
    """
    search_fields = ('course_id',)
    list_display = ('course_id', 'modified')
    ordering = ('course_id', '-modified')


admin.site.register(CourseStructure, CourseStructureAdmin)

"""
Admin configurations for course_meta app
"""
from django.contrib import admin

from .models import CourseMeta


class CourseMetaAdmin(admin.ModelAdmin):
    """
    Django admin customizations for CourseMeta model
    """

    list_display = ('course_id', 'is_prereq')
    search_fields = ('course_id',)


admin.site.register(CourseMeta, CourseMetaAdmin)

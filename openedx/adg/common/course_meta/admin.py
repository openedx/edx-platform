"""
Admin site bindings for course_meta models
"""
from django.contrib import admin

from .models import CourseMeta


@admin.register(CourseMeta)
class CourseMetaAdmin(admin.ModelAdmin):
    """
    Django admin customizations for CourseMeta model
    """

    readonly_fields = ('short_id',)
    list_display = ('course_id', 'short_id')
    search_fields = ('course_id',)

"""
django admin pages for course_structures model
"""

from django.contrib import admin

from .models import CourseStructure


class CourseStructureAdmin(admin.ModelAdmin):
    search_fields = ('course_id',)
    list_display = ('course_id', 'modified')
    ordering = ('course_id', '-modified')


admin.site.register(CourseStructure, CourseStructureAdmin)

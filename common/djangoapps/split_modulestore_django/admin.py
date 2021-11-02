"""
Admin registration for Split Modulestore Django Backend
"""
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import SplitModulestoreCourseIndex


@admin.register(SplitModulestoreCourseIndex)
class SplitModulestoreCourseIndexAdmin(SimpleHistoryAdmin):
    """
    Admin config for course indexes
    """
    list_display = ('course_id', 'draft_version', 'published_version', 'library_version', 'wiki_slug', 'last_update')
    search_fields = ('course_id', 'wiki_slug')
    ordering = ('course_id', )
    readonly_fields = ('id', 'objectid', 'course_id', 'org', )

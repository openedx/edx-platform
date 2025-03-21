"""
This module contains the admin configuration for the CourseToLibraryImport model.
"""

from django.contrib import admin

from .models import CourseToLibraryImport

# Run a task to import courses to the library
# This task is run by the celery worker to import courses to the library.


class CourseToLibraryImportAdmin(admin.ModelAdmin):
    """
    Admin configuration for the CourseToLibraryImport model.
    """

    list_display = (
        'id',
        'status',
        'course_ids',
        'library_key',
    )
    list_filter = (
        'status',
    )
    search_fields = (
        'course_ids',
        'library_key',
    )

    raw_id_fields = ('user',)


admin.site.register(CourseToLibraryImport, CourseToLibraryImportAdmin)

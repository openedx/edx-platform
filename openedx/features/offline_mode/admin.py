"""
Offline mode admin configuration.
"""
from django.contrib import admin

from .models import OfflineCourseSize


class OfflineCourseSizeAdmin(admin.ModelAdmin):
    """
    OfflineCourseSize admin configuration.
    """

    list_display = ("course_id", "size")
    search_fields = ("course_id",)


admin.site.register(OfflineCourseSize, OfflineCourseSizeAdmin)

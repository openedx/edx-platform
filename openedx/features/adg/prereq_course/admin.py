"""
Admin configurations for prereq_course app
"""
from django.contrib import admin

from .models import PrereqCourse


class PrereqCourseAdmin(admin.ModelAdmin):
    """
    Djanog admin customizations for PrereqCourse model
    """

    list_display = ('course_id', 'is_enabled')
    search_fields = ('course_id',)


admin.site.register(PrereqCourse, PrereqCourseAdmin)

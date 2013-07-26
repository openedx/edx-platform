"""
Django admin page for bulk email models
"""
from django.contrib import admin

from bulk_email.models import CourseEmail, Optout


class CourseEmailAdmin(admin.ModelAdmin):
    """Admin for course email."""
    readonly_fields = ('sender',)


class OptoutAdmin(admin.ModelAdmin):
    """Admin for optouts."""
    list_display = ('email', 'course_id')


admin.site.register(CourseEmail, CourseEmailAdmin)
admin.site.register(Optout, OptoutAdmin)

"""
django admin page for the course creators table
"""

from course_creators.models import CourseCreator
from django.contrib import admin


class CourseCreatorAdmin(admin.ModelAdmin):
    list_display = ('username', 'state', 'state_changed', 'note')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff


admin.site.register(CourseCreator, CourseCreatorAdmin)

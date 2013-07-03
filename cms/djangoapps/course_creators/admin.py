"""
django admin page for the course creators table
"""

from course_creators.models import CourseCreator
from django.contrib import admin


class CourseCreatorAdmin(admin.ModelAdmin):
    # Fields to display on the overview page.
    list_display = ('username', 'email', 'state', 'state_changed')
    readonly_fields = ('username', 'email', 'state_changed')
    # Controls the order on the edit form (without this, read-only fields appear at the end).
    fieldsets = (
        (None, {
            'fields': list_display
        }),
    )
    # Fields that filtering support
    list_filter = list_display
    # Fields that search supports. Note that the search term for state has to be
    # its key (ie, 'g' instead of 'granted').
    search_fields = ['username', 'email', 'state']
    # Turn off the action bar (we have no bulk actions)
    actions = None

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def save_model(self, request, obj, form, change):
        # Store who is making the request.
        obj.admin = request.user
        obj.save()


admin.site.register(CourseCreator, CourseCreatorAdmin)

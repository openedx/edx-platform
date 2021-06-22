"""Admin panel for Completion API and Progress Stats"""

from completion.models import BlockCompletion
from django.contrib import admin

from openedx.features.pakx.lms.overrides.models import CourseProgressStats


class BlockCompletionAdmin(admin.ModelAdmin):
    """
    Admin interface for the BlockCompletion object.
    """
    list_display = ('user', 'context_key', 'block_type', 'block_key', 'completion', 'created', 'modified')
    search_fields = ('user__username', 'block_type')

    class Meta(object):
        """
        Meta class for BlockCompletion admin model
        """
        model = BlockCompletion


admin.site.register(BlockCompletion, BlockCompletionAdmin)


@admin.register(CourseProgressStats)
class CourseProgressStatsAdmin(admin.ModelAdmin):
    """
    Admin interface for CourseProgressStats object
    """

    list_display = ['user', 'course_id', 'email_reminder_status', 'progress', 'grade', 'completion_date']
    search_fields = ['email_reminder_status', 'course_id', 'progress']
    list_filter = ['email_reminder_status', 'course_id', 'progress']

from django.contrib import admin

from completion.models import BlockCompletion
from openedx.features.pakx.lms.overrides.models import CourseProgressEmailModel


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


@admin.register(CourseProgressEmailModel)
class CourseProgressEmailModelAdmin(admin.ModelAdmin):
    """
    Admin interface for CourseProgressEmailModel object
    """

    list_display = ['user', 'course_id', 'status']
    search_fields = ['status', 'course_id']
    list_filter = ['status', 'course_id']

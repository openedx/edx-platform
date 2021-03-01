from django.contrib import admin

from completion.models import BlockCompletion


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

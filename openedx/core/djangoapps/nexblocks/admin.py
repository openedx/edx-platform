"""
Admin site bindings for contentstore
"""

from django.contrib import admin

from .models import NexBlockLearnerData


@admin.register(NexBlockLearnerData)
class NexBlockLearnerDataAdmin(admin.ModelAdmin):
    list_display = ("learning_context_key", "block_type", "value")
    search_fields = (
        "learning_context_key",
        "block_type",
    )

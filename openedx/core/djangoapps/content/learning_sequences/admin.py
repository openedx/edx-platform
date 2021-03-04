"""
Read-only Django Admin for viewing Learning Sequences and Outline data.
"""
from datetime import datetime
from enum import Enum
import json

from django.contrib import admin
from django.utils.html import format_html
from opaque_keys import OpaqueKey
import attr

from .api import get_course_outline
from .models import LearningContext


class LearningContextAdmin(admin.ModelAdmin):
    """
    This is a read-only model admin that is meant to be useful for querying.

    Writes are disabled, because:

    1. These values are auto-built/updated based on course publishes.
    2. These are read either the Studio or LMS process, but it's only supposed
       to be written to from the Studio process.
    """
    list_display = (
        'context_key',
        'title',
        'published_at',
        'published_version',
        'modified'
    )
    readonly_fields = (
        'context_key',
        'title',
        'published_at',
        'published_version',
        'created',
        'modified',
        'outline',
    )
    search_fields = ['context_key', 'title']
    actions = None

    def outline(self, obj):
        """
        Computed attribute that shows the outline JSON in the detail view.
        """
        def json_serializer(_obj, _field, value):
            if isinstance(value, OpaqueKey):
                return str(value)
            elif isinstance(value, Enum):
                return value.value
            elif isinstance(value, datetime):
                return value.isoformat()
            return value

        outline_data = get_course_outline(obj.context_key)
        outline_data_dict = attr.asdict(
            outline_data,
            recurse=True,
            value_serializer=json_serializer,
        )
        outline_data_json = json.dumps(outline_data_dict, indent=2, sort_keys=True)
        return format_html("<pre>\n{}\n</pre>", outline_data_json)

    def has_add_permission(self, request):
        """
        Disallow additions. See docstring for has_change_permission()
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        Disallow edits.

        This app rebuilds automatically based off of course publishes. Any
        manual edits will be wiped out the next time someone touches the course,
        so it's better to disallow this in the admin rather than to pretend this
        works and have it suddenly change back when someone edits the course.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Disallow deletes.

        Deleting these models can have far reaching consequences and delete a
        lot of related data in other parts of the application/project. We should
        only do update through the API, which allows us to rebuild the outlines.
        """
        return False


admin.site.register(LearningContext, LearningContextAdmin)

"""
Admin site for content libraries
"""
from django.contrib import admin
from .models import ContentLibrary, ContentLibraryPermission


class ContentLibraryPermissionInline(admin.TabularInline):
    """
    Inline form for a content library's permissions
    """
    model = ContentLibraryPermission
    raw_id_fields = ("user", "group", )
    extra = 0


@admin.register(ContentLibrary)
class ContentLibraryAdmin(admin.ModelAdmin):
    """
    Definition of django admin UI for Content Libraries
    """
    fields = ("library_key", "org", "slug", "bundle_uuid", "allow_public_learning", "allow_public_read")
    list_display = ("slug", "org", "bundle_uuid")
    inlines = (ContentLibraryPermissionInline, )

    def get_readonly_fields(self, request, obj=None):
        """
        Ensure that 'slug' and 'uuid' cannot be edited after creation.
        """
        if obj:
            return ["library_key", "org", "slug", "bundle_uuid"]
        else:
            return ["library_key", ]

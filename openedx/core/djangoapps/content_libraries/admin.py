"""
Admin site for content libraries
"""
from django.contrib import admin
from .models import (
    ContentLibrary,
    ContentLibraryPermission,
    LegacyLibraryMigrationSource,
    LegacyLibraryMigration,
    LegacyLibraryBlockMigration,
)


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

    fields = (
        "library_key",
        "org",
        "slug",
        "allow_public_learning",
        "allow_public_read",
        "authorized_lti_configs",
    )
    list_display = ("slug", "org",)
    inlines = (ContentLibraryPermissionInline, )

    def get_readonly_fields(self, request, obj=None):
        """
        Ensure that 'slug' and 'uuid' cannot be edited after creation.
        """
        if obj:
            return ["library_key", "org", "slug"]
        else:
            return ["library_key", ]


class LegacyLibraryBlockMigrationInline(admin.TabularInline):
    """
    Django admin UI for content library block migrations
    """
    model = LegacyLibraryBlockMigration
    list_display = ("library_migration", "source_key", "target")  # @@TODO


@admin.register(LegacyLibraryMigration)
class LegacyLibraryMigrationAdmin(admin.ModelAdmin):
    """
    Django admin UI for content library migrations
    """
    model = LegacyLibraryMigration
    list_display = ("source", "target_library", "target_collection")
    inlines = (LegacyLibraryBlockMigrationInline,)


class LegacyLibraryMigrationInline(admin.ModelAdmin):
    """
    Django admin UI for content library migrations
    """
    model = LegacyLibraryMigration
    list_display = ("target_library", "target_collection")  # @@TODO show names?


@admin.register(LegacyLibraryMigrationSource)
class LegacyLibraryMigrationSourceAdmin(admin.ModelAdmin):
    """
    @@TODO
    """
    model = LegacyLibraryMigrationSource
    list_display = ("library_key", "authoritative_migration")  # @@TODO fk display
    inlines = (LegacyLibraryMigrationInline,)  # @@TODO does this just work?

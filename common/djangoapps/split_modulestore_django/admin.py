"""
Admin registration for Split Modulestore Django Backend
"""
import logging

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import LibraryLocator as LegacyLibraryLocator, LibraryLocatorV2, LibraryCollectionLocator
from simple_history.admin import SimpleHistoryAdmin

from openedx.core.djangoapps.content_libraries.migration_api import migrate_legacy_library

from .models import SplitModulestoreCourseIndex


logger = logging.getLogger(__name__)


@admin.action(description="Migrate Legacy Library to new Library or Collection")
def migrate(modeladmin, request, queryset):
    """
    Migrate legacy modulestore index entries to Learning Core, based on `migration_target_key`.

    Currently, this only works for LEGACY LIBRARY (library-v1:...) index entries.
    Will fail if used on any other course entry.

    The only valid targets are currently V2 Libraries and their Collections.
    Will fail on any other type of target key.

    WARNING: This does not delete the remaining legacy index item! It's up to Studio to recognize that an item has been
    migrated, and that the legacy entry should be ignored.
    """
    target_key_string = request.POST['migration_target_key']
    target_library_key: LibraryLocatorV2
    target_collection_slug: str | None
    try:
        target_library_key = LibraryLocatorV2.from_string(target_key_string)
        target_collection_slug = None
    except InvalidKeyError:
        try:
            target_collection_key = LibraryCollectionLocator.from_string(target_key_string)
            target_library_key = target_collection_key.library_key
            target_collection_slug = target_collection_key.collection_id
        except InvalidKeyError:
            modeladmin.message_user(
                request,
                f"Migration target key is not a valid V2 Library or Collection key: {target_key_string}",
                level=messages.ERROR,
            )
            return
    for obj in queryset:
        if not isinstance(obj.course_id, LegacyLibraryLocator):
            modeladmin.message_user(
                request,
                f"Selected entry is not a Legacy Library: {obj.course_id}. Skipping.",
                level=messages.WARNING,
            )
            continue
        try:
            migrate_legacy_library(
                source_key=obj.course_id,
                target_key=target_library_key,
                collection_slug=target_collection_slug,
                user=request.user,
            )
        except Exception as exc:  # pylint: disable=broad-except
            modeladmin.message_user(
                request,
                f"Failed to migrate {obj.course_id} to {target_key_string}: {exc}. See logs for details.",
                level=messages.ERROR,
            )
            logger.exception(exc)
            continue
        else:
            modeladmin.message_user(
                request,
                f"Migrated {obj.course_id} to {target_key_string}",
                level=messages.SUCCESS,
            )


class MigrationTargetForm(ActionForm):
    migration_target_key = forms.CharField()


@admin.register(SplitModulestoreCourseIndex)
class SplitModulestoreCourseIndexAdmin(SimpleHistoryAdmin):
    """
    Admin config for course indexes
    """
    list_display = ('course_id', 'draft_version', 'published_version', 'library_version', 'wiki_slug', 'last_update')
    search_fields = ('course_id', 'wiki_slug')
    ordering = ('course_id', )
    actions = [migrate]
    action_form = MigrationTargetForm

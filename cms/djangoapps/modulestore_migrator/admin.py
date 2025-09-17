"""
A nice little admin interface for migrating courses and libraries from modulstore to Learning Core.
"""
import logging

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.db import models


from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import LibraryCollectionLocator, LibraryLocatorV2
from user_tasks.models import UserTaskStatus

from openedx.core.types.http import AuthenticatedHttpRequest

from . import api
from .data import CompositionLevel
from .models import ModulestoreSource, ModulestoreMigration, ModulestoreBlockSource, ModulestoreBlockMigration


log = logging.getLogger(__name__)


class StartMigrationTaskForm(ActionForm):
    """
    Params for start_migration_task admin adtion, displayed next the "Go" button.
    """
    target_key = forms.CharField(label="Target library or collection key:", required=False)
    replace_existing = forms.BooleanField(label="Replace existing content", required=False)
    composition_level = forms.ChoiceField(
        label="Aggregate up to:", choices=CompositionLevel.supported_choices, required=False
    )


def task_status_details(obj: ModulestoreMigration) -> str:
    """
    Return details about the status of the migration, falling back to `task_status.state` if no details.
    """
    if obj.task_status.state == UserTaskStatus.FAILED:
        # Calling fail(msg) from a task should automatically generates an "Error" artifact with that msg.
        # https://django-user-tasks.readthedocs.io/en/latest/user_tasks.html#user_tasks.models.UserTaskStatus.fail
        if error_artifacts := obj.task_status.artifacts.filter(name="Error"):
            if error_text := error_artifacts.order_by("-created").first().text:
                return error_text
    elif obj.task_status.state == UserTaskStatus.SUCCEEDED:
        return f"Successfully migrated {obj.block_migrations.count()} blocks"
    return obj.task_status.state


migration_admin_fields = (
    "target",
    "target_collection",
    "task_status",
    # The next line works, but django-stubs incorrectly thinks that these should all be strings,
    # so we will need to use type:ignore below.
    task_status_details,
    "composition_level",
    "replace_existing",
    "change_log",
    "staged_content",
)


class ModulestoreMigrationInline(admin.TabularInline):
    """
    Readonly table within the ModulestoreSource page; each row is a Migration from this Source.
    """
    model = ModulestoreMigration
    fk_name = "source"
    show_change_link = True
    readonly_fields = migration_admin_fields  # type: ignore[assignment]

    def has_add_permission(self, _request, _obj):
        return False


class ModulestoreBlockSourceInline(admin.TabularInline):
    """
    Readonly table within the ModulestoreSource page; each row is a BlockSource.
    """
    model = ModulestoreBlockSource
    fk_name = "overall_source"
    readonly_fields = (
        "key",
        "forwarded_by"
    )

    def has_add_permission(self, _request, _obj):
        return False


@admin.register(ModulestoreSource)
class ModulestoreSourceAdmin(admin.ModelAdmin):
    """
    Admin interface for source legacy libraries and courses.
    """
    readonly_fields = ("forwarded_by",)
    list_display = ("id", "key", "forwarded_by")
    actions = ["start_migration_task"]
    action_form = StartMigrationTaskForm
    inlines = [ModulestoreMigrationInline, ModulestoreBlockSourceInline]

    @admin.action(description="Start migration for selected sources")
    def start_migration_task(
        self,
        request: AuthenticatedHttpRequest,
        queryset: models.QuerySet[ModulestoreSource],
    ) -> None:
        """
        Start a migration for each selected source
        """
        form = StartMigrationTaskForm(request.POST)
        if not form.is_valid():
            # @@TODO Better messaging of form errors
            messages.add_message(request, messages.ERROR, f"Invalid action params: {form.errors}")
        target_key_string = form.cleaned_data['target_key']
        if not target_key_string:
            messages.add_message(request, messages.ERROR, "Target key is required")
            return
        try:
            target_library_key = LibraryLocatorV2.from_string(target_key_string)
            target_collection_slug = None
        except InvalidKeyError:
            try:
                target_collection_key = LibraryCollectionLocator.from_string(target_key_string)
                target_library_key = target_collection_key.lib_key
                target_collection_slug = target_collection_key.collection_id
            except InvalidKeyError:
                messages.add_message(request, messages.ERROR, f"Invalid target key: {target_key_string}")
                return
        started = 0
        total = 0
        for source in queryset:
            total += 1
            try:
                api.start_migration_to_library(
                    user=request.user,
                    source_key=source.key,
                    target_library_key=target_library_key,
                    target_collection_slug=target_collection_slug,
                    composition_level=form.cleaned_data['composition_level'],
                    replace_existing=form.cleaned_data['replace_existing'],
                    forward_source_to_target=False,
                )
            except Exception as exc:  # pylint: disable=broad-except
                message = f"Failed to start migration {source.key} -> {target_key_string}"
                messages.add_message(request, messages.ERROR, f"{message}: {exc}")
                log.exception(message)
                continue
            started += 1
        click_in = "Click into the source objects to see migration details."

        if not started:
            messages.add_message(request, messages.WARNING, f"Failed to start {total} migration(s).")
        if started < total:
            messages.add_message(request, messages.WARNING, f"Started {started} of {total} migration(s). {click_in}")
        else:
            messages.add_message(request, messages.INFO, f"Started {started} migration(s). {click_in}")


class ModulestoreBlockMigrationInline(admin.TabularInline):
    """
    Readonly table witin the Migration admin; each row is a block
    """
    model = ModulestoreBlockMigration
    fk_name = "overall_migration"
    readonly_fields = (
        "source",
        "target",
        "change_log_record",
    )
    list_display = ("id", *readonly_fields)


@admin.register(ModulestoreMigration)
class ModulestoreMigrationAdmin(admin.ModelAdmin):
    """
    Readonly admin page for viewing Migrations
    """
    readonly_fields = ("source", *migration_admin_fields)  # type: ignore[assignment]
    list_display = ("id", "source", *migration_admin_fields)  # type: ignore[assignment]
    inlines = [ModulestoreBlockMigrationInline]
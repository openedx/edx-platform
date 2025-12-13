"""
API for migration from modulestore to learning core
"""
from __future__ import annotations

import typing as t
from uuid import UUID

from celery.result import AsyncResult
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2, BlockUsageLocator
from openedx_learning.api.authoring import get_collection

from openedx.core.djangoapps.content_libraries.api import get_library
from openedx.core.types.user import AuthUser

from .data import (
    SourceContextKey, ModulestoreMigration, ModulestoreBlockMigration, ModulestoreSuccessfulBlockMigration
)
from . import tasks, models


def start_migration_to_library(
    *,
    user: AuthUser,
    source_key: SourceContextKey,
    target_library_key: LibraryLocatorV2,
    target_collection_slug: str | None = None,
    create_collection: bool = False,
    composition_level: str,
    repeat_handling_strategy: str,
    preserve_url_slugs: bool,
    forward_source_to_target: bool,
) -> AsyncResult:
    """
    Import a course or legacy library into a V2 library (or, a collection within a V2 library).
    """
    return start_bulk_migration_to_library(
        user=user,
        source_key_list=[source_key],
        target_library_key=target_library_key,
        target_collection_slug_list=[target_collection_slug],
        create_collections=create_collection,
        composition_level=composition_level,
        repeat_handling_strategy=repeat_handling_strategy,
        preserve_url_slugs=preserve_url_slugs,
        forward_source_to_target=forward_source_to_target,
    )


def start_bulk_migration_to_library(
    *,
    user: AuthUser,
    source_key_list: list[SourceContextKey],
    target_library_key: LibraryLocatorV2,
    target_collection_slug_list: list[str | None] | None = None,
    create_collections: bool = False,
    composition_level: str,
    repeat_handling_strategy: str,
    preserve_url_slugs: bool,
    forward_source_to_target: bool,
) -> AsyncResult:
    """
    Import a list of courses or legacy libraries into a V2 library (or, a collections within a V2 library).
    """
    target_library = get_library(target_library_key)
    # get_library ensures that the library is connected to a learning package.
    target_package_id: int = target_library.learning_package_id  # type: ignore[assignment]

    sources_pks: list[int] = []
    for source_key in source_key_list:
        source, _ = models.ModulestoreSource.objects.get_or_create(key=source_key)
        sources_pks.append(source.id)

    target_collection_pks: list[int | None] = []
    if target_collection_slug_list:
        for target_collection_slug in target_collection_slug_list:
            if target_collection_slug:
                target_collection_id = get_collection(target_package_id, target_collection_slug).id
                target_collection_pks.append(target_collection_id)
            else:
                target_collection_pks.append(None)

    return tasks.bulk_migrate_from_modulestore.delay(
        user_id=user.id,
        sources_pks=sources_pks,
        target_library_key=str(target_library_key),
        target_collection_pks=target_collection_pks,
        create_collections=create_collections,
        composition_level=composition_level,
        repeat_handling_strategy=repeat_handling_strategy,
        preserve_url_slugs=preserve_url_slugs,
        forward_source_to_target=forward_source_to_target,
    )


def get_authoritative_block_migration(source_key: UsageKey) -> ModulestoreSuccessfulBlockMigration | None:
    """
    Figure out how a given source block has been 'officially' migrated, if at all.

    Note: This function may return None for a block which *has* been migrated 1+ times.
          This just means that those migrations were non-authoritative (i.e., imports rather
          than true migrations).

    # @@TODO shouldn't this go through block-level forwarded, so that future partial migrations that don't
    #        migrate the block don't un-migrate it?
    """
    if not isinstance(source_key, BlockUsageLocator):
        # Only blocks from v1 courses and legacy libraries can have migrations.
        return None
    if not (migration := _get_authoritative_migration_model(source_key.course_key)):
        return None
    try:
        block_migration = ModulestoreBlockMigration.from_model(
            migration.block_migrations.get(source__key=source_key),
        )
    except models.ModulestoreBlockMigration.DoesNotExist:
        return None
    return (
        block_migration
        if isinstance(block_migration, ModulestoreSuccessfulBlockMigration)
        else None  # Failed migrations cannot be authoritative
    )


def get_block_migrations(
    *,
    source_key: UsageKey,
    target_context_key: LibraryLocatorV2 | None = None,
    successful: bool | None = None,
) -> t.Iterable[ModulestoreBlockMigration]:
    """
    Fetch info on all the ways this block as been migrated, including non-authoritatively.
    """
    if not isinstance(source_key, BlockUsageLocator):
        # Only blocks from v1 courses and legacy libraries can have migrations.
        return []
    block_migrations = models.ModulestoreBlockMigration.objects.filter(source__key=source_key)
    if target_context_key:
        block_migrations = block_migrations.filter(overall_migration__target__key=str(target_context_key))
    if successful is not None:
        block_migrations = block_migrations.filter(target__isnull=(not successful))
    return (
        ModulestoreBlockMigration.from_model(block_migration)
        for block_migration in block_migrations
    )


def get_authoritative_migration(source_key: SourceContextKey) -> ModulestoreMigration | None:
    """
    Get info on the migration which 'officially' forwards the source to a new learning context.

    If no such successful migration exists, returns None.

    Note: This function may return None for a course or legacy lib that *has* been migrated 1+ times.
          This just means that those migrations were non-authoritative (i.e., imports rather
          than true migrations).
    """
    if not (migration := _get_authoritative_migration_model(source_key)):
        return None
    return ModulestoreMigration.from_model(migration)


def get_preferred_migration(
    source_key: SourceContextKey,
    *,
    target_key: LibraryLocatorV2 | None = None,
) -> ModulestoreMigration | None:
    """
    Given a source and a target, get the "best" successful migration to repsect.

    When there is a matching authoritative migration for the source, use that one.
    Otherwise, use the oldest matching migration.
    If there are no matching migrations, return None.

    This is useful in scenarios when a course/legacy lib may have been migrated an arbitrary
    number of times to an arbitrary number of different targets, and you *need* to pick exactly
    one to respect, whether or not an authoritative one exists and is relevant to the target.
    """
    if authoritative := get_authoritative_migration(source_key):
        if (not target_key) or authoritative.target_key == target_key:
            # There is an authoritative migration, and it matches all the filters! Use it.
            return authoritative
    matching_migrations = get_migrations(
        source_key=source_key,
        target_key=target_key,
        successful=True,
    )
    try:
        return next(iter(matching_migrations))  # Return the earliest match
    except StopIteration:
        return None  # No matches


def get_migrations(
    source_key: SourceContextKey | None = None,
    *,
    target_key: LibraryLocatorV2 | None = None,
    target_collection_slug: str | None = None,
    task_uuid: UUID | None = None,
    successful: bool | None = None,
) -> t.Iterable[ModulestoreMigration]:
    """
    Given some criteria, get all modulestore->LearningCore migrations.

    Returns an iterable, ordered from oldest to newest.

    Please note: If you provide no filters, this will return an iterable across the whole
                 ModulestoreMigration table. Please paginate thoughtfully if you do that.
    """
    migrations = models.ModulestoreMigration.objects.all()
    if source_key:
        migrations = migrations.filter(source__key=source_key)
    if target_key:
        migrations = migrations.filter(target__key=str(target_key))
    if target_collection_slug:
        migrations = migrations.filter(target_collection__key=target_collection_slug)
    if task_uuid:
        migrations = migrations.filter(task_status__uuid=task_uuid)
    if successful is not None:
        migrations = migrations.filter(is_failed=(not successful))
    return (
        ModulestoreMigration.from_model(migration)
        for migration in migrations.order_by("id")  # primary key is a proxy for newness
    )


def _get_authoritative_migration_model(source_key: SourceContextKey) -> models.ModulestoreMigration | None:
    """
    Same as get_authoritative_migration, but returns the db model
    """
    try:
        source = models.ModulestoreSource.objects.get(key=str(source_key))
    except models.ModulestoreSource.DoesNotExist:
        return None
    if not source.forwarded:
        return None
    migration: models.ModulestoreMigration = source.forwarded
    if migration.is_failed:
        return None
    return migration

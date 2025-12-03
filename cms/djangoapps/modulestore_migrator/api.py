"""
API for migration from modulestore to learning core
"""
from __future__ import annotations

import typing as t
from dataclasses import dataclass
from uuid import UUID

from celery.result import AsyncResult
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import (
    CourseLocator, LibraryLocator,
    LibraryLocatorV2, LibraryUsageLocatorV2,
    LibraryContainerLocator,
)
from openedx_learning.api.authoring import get_collection
from openedx_learning.api.authoring_models import Container

from openedx.core.djangoapps.content_libraries.api import get_library, library_component_usage_key
from openedx.core.types.user import AuthUser

from . import tasks, models


__all__ = (
    "SourceContextKey",
    "ModulestoreMigration",
    "ModulestoreBlockMigration",
    "ModulestoreComponentMigration",
    "ModulestoreContainerMigration",
    "ModulestoreFailedBlockMigration",
    "ModulestoreMigrationBlockMappings",
    "get_authoritative_block_migration",
    "get_authoritative_migration",
    "get_migrations",
)


SourceContextKey: t.TypeAlias = CourseLocator | LibraryLocator


@dataclass(frozen=True)
class ModulestoreMigration:
    """
    Metadata on a migration of a course or legacy library to a v2 library in learning core.
    """
    source_key: SourceContextKey
    target_key: LibraryLocatorV2
    target_title: str
    target_collection_slug: str | None
    target_collection_title: str | None
    is_authoritative: bool
    task_uuid: UUID  # the UserTask which executed this migration

    @classmethod
    def from_model(cls, m: ModulestoreMigration) -> t.Self:
        return cls(
            source_key=m.source.key,
            target_key=m.target.key,
            target_title=m.target.title,
            target_collection_slug=m.target_collection.key,
            target_collection_title=m.target_collection.title,
            is_authoritative=(m.id == m.source.forwarded_id),
            task_uuid=m.task_uuid,
        )

    def load_block_mappings(self) -> ModulestoreMigrationBlockMappings:
        """
        Get details about the migrations of each individual block within a course/lib migration.
        """
        block_migrations = [
            ModulestoreBlockMigration.from_model(block_migration)
            for block_migration in self.block_migrations.select_related(
                'target__component__component_type',
                'target__container'
                'target__learning_package'
            )
        ]
        return ModulestoreMigrationBlockMappings(
            component_migrations={
                bm.source_key: bm for bm in block_migrations
                if isinstance(bm, ModulestoreComponentMigration)
            },
            container_migrations={
                bm.source_key: bm for bm in block_migrations
                if isinstance(bm, ModulestoreContainerMigration)
            },
            failed_block_migrations={
                bm.source_key: bm for bm in block_migrations
                if isinstance(bm, ModulestoreFailedBlockMigration)
            },
        )


@dataclass(frozen=True)
class ModulestoreMigrationBlockMappings:
    """
    Details on a migration of a course or legacy library to a v2 library in learning core.

    In each of the dicts, the keys are the usage keys of the source blocks.
    """
    component_migrations: dict[UsageKey, ModulestoreComponentMigration]
    container_migrations: dict[UsageKey, ModulestoreContainerMigration]
    failed_block_migrations: dict[UsageKey, ModulestoreFailedBlockMigration]

    @property
    def all_migrations(self) -> dict[UsageKey, ModulestoreBlockMigration]:
        return {
            **self.component_migrations,
            **self.container_migrations,
            **self.failed_block_migrations,
        }


@dataclass(frozen=True)
class ModulestoreBlockMigration:
    """
    Base class for a modulestore block that's been migrated to Learning Core.
    """
    source_key: UsageKey
    target_key: LibraryUsageLocatorV2 | LibraryContainerLocator | None  # None iff failed
    target_title: str | None  # None iff failed
    target_version_num: int | None  # None iff failed OR unknown
    unsupported_reason: str | None  # None iff successful

    @classmethod
    def from_model(cls, m: models.ModulestoreBlockMigration) -> t.Self:
        """
        Build an instance of this class from a database row
        """
        library_key: LibraryUsageLocatorV2 = m.overall_migration.target.content_library.key
        if not m.target:
            return ModulestoreFailedBlockMigration(
                source_key=m.source.key,
                target_key=None,
                target_title=None,
                target_version_num=None,
                unsupported_reason=m.unsupported_reason,
            )
        if hasattr(m.target, "component"):
            return ModulestoreComponentMigration(
                source_key=m.source.key,
                target_key=library_component_usage_key(library_key, m.target.component),
                target_title=m.target.title,
                target_version_num=m.change_log_record.version_num if m.change_log_record else None,
                unsupported_reason=None,
            )
        elif hasattr(m.target, "container"):
            return ModulestoreContainerMigration(
                source_key=m.source.key,
                target_key=_library_container_key(library_key, m.target.container),
                target_title=m.target.title,
                target_version_num=m.change_log_record.version_num if m.change_log_record else None,
                unsupported_reason=None,
            )
        else:
            raise NotImplementedError(f"Entity is neither a container nor component: {m.target}")


@dataclass(frozen=True)
class ModulestoreComponentMigration(ModulestoreBlockMigration):
    """
    Info on a modulestore block which has been migrated into a LC component
    """
    target_key: LibraryUsageLocatorV2
    target_title: str
    target_version_num: int | None
    unsupported_reason: None


@dataclass(frozen=True)
class ModulestoreContainerMigration(ModulestoreBlockMigration):
    """
    Info on a modulestore structural block which has been migrated into a LC container
    """
    target_key: LibraryContainerLocator
    target_title: str
    target_version_num: int | None
    unsupported_reason: None


@dataclass(frozen=True)
class ModulestoreFailedBlockMigration(ModulestoreBlockMigration):
    """
    Info on a modulestore block which failed to be migrated into LC
    """
    target_key: None
    target_title: None
    target_version_num: None
    unsupported_reason: str


def _library_container_key(library_key: LibraryLocatorV2, container: Container) -> LibraryContainerLocator:
    """
    @@TODO
    """
    _ = library_key, container
    raise NotImplementedError()


def start_migration_to_library(
    *,
    user: AuthUser,
    source_key: SourceContextKey,
    target_library_key: LibraryLocatorV2,
    target_collection_slug: str | None = None,
    composition_level: str,
    repeat_handling_strategy: str,
    preserve_url_slugs: bool,
    forward_source_to_target: bool,
) -> AsyncResult:
    """
    Import a course or legacy library into a V2 library (or, a collection within a V2 library).
    """
    source, _ = models.ModulestoreSource.objects.get_or_create(key=source_key)
    target_library = get_library(target_library_key)
    # get_library ensures that the library is connected to a learning package.
    target_package_id: int = target_library.learning_package_id  # type: ignore[assignment]
    target_collection_id = None

    if target_collection_slug:
        target_collection_id = get_collection(target_package_id, target_collection_slug).id

    return tasks.migrate_from_modulestore.delay(
        user_id=user.id,
        source_pk=source.id,
        target_library_key=str(target_library_key),
        target_collection_pk=target_collection_id,
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


def get_authoritative_block_migration(source_key: UsageKey) -> ModulestoreBlockMigration | None:
    """
    Figure out how a given source block has been 'officially' migrated, if at all.

    Note: This function may return None for a block which *has* been migrated 1+ times.
          This just means that those migrations were non-authoritative (i.e., imports rather
          than true migrations).
    """
    if not (migration := _get_authoritative_migration_model(source_key)):
        return None
    try:
        return ModulestoreBlockMigration.from_model(
            migration.block_migrations.get(source__key=source_key)
        )
    except models.ModulestoreBlockMigration.DoesNotExist:
        return None


def get_authoritative_migration(source_key: SourceContextKey) -> ModulestoreMigration | None:
    """
    Get info on the migration which 'officially' forwards the source to a new learning context.

    If no such migration exists, returns None.
    If only a failed migration exists, returns None unless include_failed=True is specified.

    Note: This function may return None for a course or legacy lib that *has* been migrated 1+ times.
          This just means that those migrations were non-authoritative (i.e., imports rather
          than true migrations).
    """
    if not (migration := _get_authoritative_migration_model(source_key)):
        return None
    return ModulestoreMigration.from_model(migration)


def get_migrations(
    *,
    source_key: SourceContextKey | None = None,
    target_key: LibraryLocatorV2 | None = None,
    target_collection_slug: str | None = None,
    task_uuid: UUID | None = None,
    successful: bool | None = None,
) -> t.Iterable[ModulestoreMigration]:
    """
    Fetch migrations from courses and legacy libraries to V2 libraries, filtered by some criteria.

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
        migrations = migrations.filter(is_failed=successful)
    return (
        ModulestoreMigration.from_model(migration)
        for migration in migrations
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



_TODO = '''

def get_migration_info(source_keys: list[CourseKey | LibraryLocator]) -> dict:

    """
    Check if the source course/library has been migrated successfully and return the last target info
    """
    return {
        info.key: info
        for info in models.ModulestoreSource.objects.filter(
            migrations__task_status__state=UserTaskStatus.SUCCEEDED,
            migrations__is_failed=False,
            key__in=source_keys,
        )
        .values_list(
            'migrations__target__key',
            'migrations__target__title',
            'migrations__target_collection__key',
            'migrations__target_collection__title',
            'key',
            named=True,
        )
    }


def get_all_migrations_info(source_keys: list[CourseKey | LibraryLocator]) -> dict:
    """
    Get all target info of all successful migrations of the source keys
    """
    results = defaultdict(list)
    for info in models.ModulestoreSource.objects.filter(
        migrations__task_status__state=UserTaskStatus.SUCCEEDED,
        migrations__is_failed=False,
        key__in=source_keys,
    ).values(
        'migrations__target__key',
        'migrations__target__title',
        'migrations__target_collection__key',
        'migrations__target_collection__title',
        'key',
    ):
        results[info['key']].append(info)
    return dict(results)


def get_target_block_usage_keys(source_key: CourseKey | LibraryLocator) -> dict[UsageKey, LibraryUsageLocatorV2 | None]:
    """
    For given source_key, get a map of legacy block key and its new location in migrated v2 library.
    """
    query_set = models.ModulestoreBlockMigration.objects.filter(overall_migration__source__key=source_key).select_related(
        'source', 'target__component__component_type', 'target__learning_package'
    )

    def construct_usage_key(lib_key_str: str, component: Component) -> LibraryUsageLocatorV2 | None:
        try:
            lib_key = LibraryLocatorV2.from_string(lib_key_str)
        except InvalidKeyError:
            return None
        return library_component_usage_key(lib_key, component)

    # Use LibraryUsageLocatorV2 and construct usage key
    return {
        obj.source.key: construct_usage_key(obj.target.learning_package.key, obj.target.component)
        for obj in query_set
        if obj.source.key is not None and obj.target is not None
    }


def get_migration_blocks_info(
    target_key: str,
    source_key: str | None,
    target_collection_key: str | None,
    task_uuid: str | None,
    is_failed: bool | None,
):
    """
    Given the target key, and optional source key, target collection key, task_uuid and is_failed get a dictionary
    containing information about migration blocks.
    """
    filters: dict[str, str | UUID | bool] = {
        'overall_migration__target__key': target_key
    }
    if source_key:
        filters['overall_migration__source__key'] = source_key
    if target_collection_key:
        filters['overall_migration__target_collection__key'] = target_collection_key
    if task_uuid:
        filters['overall_migration__task_status__uuid'] = UUID(task_uuid)
    if is_failed is not None:
        filters['target__isnull'] = is_failed
    return models.ModulestoreBlockMigration.objects.filter(**filters)

'''
"""
API for migration from modulestore to learning core
"""
from celery.result import AsyncResult
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, LearningContextKey, UsageKey
from opaque_keys.edx.locator import LibraryLocator, LibraryLocatorV2, LibraryUsageLocatorV2
from openedx_learning.api.authoring import get_collection
from user_tasks.models import UserTaskStatus

from openedx.core.djangoapps.content_libraries.api import get_library
from openedx.core.types.user import AuthUser

from . import tasks
from .models import ModulestoreBlockMigration, ModulestoreSource

__all__ = (
    "start_migration_to_library",
    "start_bulk_migration_to_library",
    "is_successfully_migrated",
    "get_migration_info",
    "get_target_block_usage_keys",
)


def start_migration_to_library(
    *,
    user: AuthUser,
    source_key: LearningContextKey,
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
    source, _ = ModulestoreSource.objects.get_or_create(key=source_key)
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
    source_key_list: list[LearningContextKey],
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
        source, _ = ModulestoreSource.objects.get_or_create(key=source_key)
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


def is_successfully_migrated(
    source_key: CourseKey | LibraryLocator,
    source_version: str | None = None,
) -> bool:
    """
    Check if the source course/library has been migrated successfully.
    """
    filters = {"task_status__state": UserTaskStatus.SUCCEEDED}
    if source_version is not None:
        filters["source_version"] = source_version
    return ModulestoreSource.objects.get_or_create(key=str(source_key))[0].migrations.filter(**filters).exists()


def get_migration_info(source_keys: list[CourseKey | LibraryLocator]) -> dict:
    """
    Check if the source course/library has been migrated successfully and return target info
    """
    return {
        info.key: info
        for info in ModulestoreSource.objects.filter(
            migrations__task_status__state=UserTaskStatus.SUCCEEDED, key__in=source_keys
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


def get_target_block_usage_keys(source_key: CourseKey | LibraryLocator) -> dict[UsageKey, LibraryUsageLocatorV2 | None]:
    """
    For given source_key, get a map of legacy block key and its new location in migrated v2 library.
    """
    query_set = ModulestoreBlockMigration.objects.filter(overall_migration__source__key=source_key).values_list(
        'source__key', 'target__key', 'target__learning_package__key'
    )

    def construct_usage_key(lib_key_str: str, entity_key_str: str) -> LibraryUsageLocatorV2 | None:
        try:
            lib_key = LibraryLocatorV2.from_string(lib_key_str)
        except InvalidKeyError:
            return None
        try:
            # Example: xblock.v1:problem:e9eef38f5f4c49de943c83a2d5170211
            _, block_type, block_id = entity_key_str.split(':')
            # mypy thinks LibraryUsageLocatorV2 is abstract. It's not.
            return LibraryUsageLocatorV2(lib_key, block_type=block_type, usage_id=block_id)  # type: ignore[abstract]
        except ValueError:
            return None

    # Use LibraryUsageLocatorV2 and construct usage key
    return {
        usage_key: construct_usage_key(lib_key_str, entity_key_str)
        for (usage_key, entity_key_str, lib_key_str) in query_set
        if usage_key is not None
    }

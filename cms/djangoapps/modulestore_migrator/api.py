"""
API for migration from modulestore to learning core
"""
from opaque_keys.edx.locator import LibraryLocatorV2
from opaque_keys.edx.keys import CourseKey, LearningContextKey
from opaque_keys.edx.locator import LibraryLocator
from openedx_learning.api.authoring import get_collection
from celery.result import AsyncResult

from openedx.core.djangoapps.content_libraries.api import get_library
from openedx.core.types.user import AuthUser
from user_tasks.models import UserTaskStatus

from . import tasks
from .data import RepeatHandlingStrategy
from .models import ModulestoreSource


__all__ = (
    "start_migration_to_library",
    "is_successfully_migrated",
    "get_migration_info",
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
    # Can raise NotImplementedError for the Fork strategy
    assert RepeatHandlingStrategy(repeat_handling_strategy).is_implemented()

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
        target_package_pk=target_package_id,
        target_library_key=str(target_library_key),
        target_collection_pk=target_collection_id,
        composition_level=composition_level,
        repeat_handling_strategy=repeat_handling_strategy,
        preserve_url_slugs=preserve_url_slugs,
        forward_source_to_target=forward_source_to_target,
    )


def is_successfully_migrated(source_key: CourseKey | LibraryLocator) -> bool:
    """
    Check if the source course/library has been migrated successfully.
    """
    return ModulestoreSource.objects.get_or_create(key=str(source_key))[0].migrations.filter(
        task_status__state=UserTaskStatus.SUCCEEDED
    ).exists()


def get_migration_info(source_keys: list[CourseKey | LibraryLocator]) -> dict:
    """
    Check if the source course/library has been migrated successfully and return target info
    """
    return ModulestoreSource.objects.filter(
        migrations__task_status__state=UserTaskStatus.SUCCEEDED,
        key__in=source_keys
    ).prefetch_related('migrations__target').values_list(
        'migrations__target__key',
        'migrations__target__title',
        'migrations__target_collection__key',
        'migrations__target_collection__title',
        'key',
        named=True
    ).in_bulk(field_name='key')

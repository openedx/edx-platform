"""
API for migration from modulestore to learning core
"""
from opaque_keys.edx.locator import LibraryLocatorV2
from opaque_keys.edx.keys import LearningContextKey
from openedx_learning.api.authoring import get_collection

from openedx.core.djangoapps.content_libraries.api import get_library
from openedx.core.types.user import AuthUser

from . import tasks
from .data import CompositionLevel
from .models import ModulestoreSource


__all__ = (
    "start_migration_to_library",
)


def start_migration_to_library(
    *,
    user: AuthUser,
    source_key: LearningContextKey,
    target_library_key: LibraryLocatorV2,
    target_collection_slug: str | None = None,
    composition_level: CompositionLevel,
    replace_existing: bool,
    forward_source_to_target: bool,  # @@TODO - Set to False for now. Explain this better.
) -> None:
    """
    Import a course or legacy library into a V2 library (or, a collection within a V2 library).
    """
    source, _ = ModulestoreSource.objects.get_or_create(key=source_key)
    target_library = get_library(target_library_key)
    if not (target_package_id := target_library.learning_package_id):
        raise ValueError(
            f"Cannot import {source_key} into library at {target_library_key} because the "
            "library is not connected to a learning package"
        )
    target_collection_id = None
    if target_collection_slug:
        target_collection_id = get_collection(target_package_id, target_collection_slug).id
    return tasks.migrate_from_modulestore.delay(
        user_id=user.id,
        source_pk=source.id,
        target_package_pk=target_package_id,
        target_collection_pk=target_collection_id,
        composition_level=composition_level,
        replace_existing=replace_existing,
        forward_source_to_target=forward_source_to_target,
    )

"""
API for migration from modulestore to learning core
"""
from opaque_keys.edx.locator import LibraryLocatorV2, LibraryCollectionLocator
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
    *
    source_key: LearningContextKey,
    target_key: LibraryLocatorV2 | LibraryCollectionLocator,
    user: AuthUser,
    composition_level: CompositionLevel,
    replace_existing: bool,
    forward_source_to_target: bool,  # @@TODO - Set to False for now. Explain this better.
) -> None:
    """
    Import a course or legacy library into a V2 library (or, a collection within a V2 library).
    """
    source, _ = ModulestoreSource.objects.get_or_create(key=source_key)
    target_library = get_library(
        target_key.lib_key if isinstance(target_key, LibraryCollectionLocator) else target_key
    )
    if not (target_package_id := target_library.learning_package_id):
        raise ValueError(
            f"Cannot import {source_key} into library at {target_key} because the "
            "library is not connected to a learning package"
        )
    if isinstance(target_key, LibraryCollectionLocator):
        target_collection_id = get_collection(target_package_id, target_key.collection_id).id
    tasks.migrate_from_modulestore.delay(
        user_id=user.id,
        source_pk=source.id,
        target_package_pk=target_package_id,
        target_collection_pk=target_collection_id,
        composition_level=composition_level,
        replace_existing=replace_existing,
        forward_source_to_target=forward_source_to_target,
    )

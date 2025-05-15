"""
API for course to library import.
"""
from typing import Sequence

from opaque_keys.edx.keys import LearningContextKey
from user_tasks.tasks import UserTask

from .helpers import cancel_incomplete_old_imports
from .models import Import as _Import
from .tasks import import_to_library_task
from .validators import validate_usage_keys_to_import


def import_to_library(
    source_key: LearningContextKey,
    usage_ids: Sequence[str],
    target_learning_package_id: int,
    user_id: int,
    composition_level: str,
    override: bool = False,
) -> tuple[_Import, UserTask]:
    """
    Import staged content to a library from staged content.
    """
    validate_usage_keys_to_import(usage_ids)

    import_from_modulestore = _Import.objects.create(
        source_key=source_key,
        user_id=user_id,
        composition_level=composition_level,
        override=override,
    )
    cancel_incomplete_old_imports(import_from_modulestore)

    task = import_to_library_task.delay(
        import_pk=import_from_modulestore.pk,
        usage_key_strings=usage_ids,
        learning_package_id=target_learning_package_id,
        user_id=user_id,
    )
    return import_from_modulestore, task

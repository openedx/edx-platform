"""
API for course to library import.
"""
from typing import Sequence

from opaque_keys.edx.keys import LearningContextKey, UsageKey

from .helpers import cancel_incomplete_old_imports
from .models import Import as _Import
from .tasks import import_staged_content_to_library_task, save_legacy_content_to_staged_content_task
from .validators import validate_usage_keys_to_import


def stage_content_for_import(source_key: LearningContextKey, user_id: int) -> _Import:
    """
    Create a new import event to import a course to a library and save course to staged content.
    """
    import_from_modulestore = _Import.objects.create(source_key=source_key, user_id=user_id)
    cancel_incomplete_old_imports(import_from_modulestore)
    save_legacy_content_to_staged_content_task.delay_on_commit(import_from_modulestore.uuid)
    return import_from_modulestore


def import_staged_content_to_library(
    usage_ids: Sequence[str | UsageKey],
    import_uuid: str,
    target_learning_package_id: int,
    user_id: int,
    composition_level: str,
    override: bool,
) -> None:
    """
    Import staged content to a library from staged content.
    """
    validate_usage_keys_to_import(usage_ids)
    import_staged_content_to_library_task.apply_async(
        kwargs={
            'usage_key_strings': usage_ids,
            'import_uuid': import_uuid,
            'learning_package_id': target_learning_package_id,
            'user_id': user_id,
            'composition_level': composition_level,
            'override': override,
        },
    )

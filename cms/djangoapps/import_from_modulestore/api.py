"""
API for course to library import.
"""
from opaque_keys.edx.keys import LearningContextKey

from .models import Import as _Import
from .tasks import import_course_staged_content_to_library_task, save_legacy_content_to_staged_content_task
from .validators import validate_usage_keys_to_import


def create_import(source_key: LearningContextKey, user_id: int, learning_package_id: int) -> _Import:
    """
    Create a new import event to import a course to a library and save course to staged content.
    """
    import_from_modulestore = _Import.objects.create(
        source_key=source_key,
        target_change_id=learning_package_id,
        user_id=user_id,
    )
    save_legacy_content_to_staged_content_task.delay_on_commit(import_from_modulestore.uuid)
    return import_from_modulestore


def import_course_staged_content_to_library(
    usage_ids: list[str],
    import_uuid: str,
    user_id: int,
    composition_level: str,
    override: bool
) -> None:
    """
    Import staged content to a library from staged content.
    """
    validate_usage_keys_to_import(usage_ids)
    import_course_staged_content_to_library_task.apply_async(
        kwargs={
            'usage_keys_string': usage_ids,
            'import_uuid': import_uuid,
            'user_id': user_id,
            'composition_level': composition_level,
            'override': override,
        },
    )

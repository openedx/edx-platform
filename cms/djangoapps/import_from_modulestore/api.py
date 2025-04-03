"""
API for course to library import.
"""
from .models import Import as _Import
from .tasks import import_course_staged_content_to_library_task, save_legacy_content_to_staged_content_task


def import_course_staged_content_to_library(
    usage_ids: list[str],
    import_uuid: str,
    user_id: int,
    composition_level: str,
    override: bool
) -> None:
    """
    Import staged content to a library.
    """
    import_course_staged_content_to_library_task.delay(
        usage_ids,
        import_uuid,
        user_id,
        composition_level,
        override,
    )


def create_import(source_key, user_id: int, learning_package_id: int) -> _Import:
    """
    Create a new import task to import a course to a library.
    """
    import_from_modulestore = _Import(
        source_key=source_key,
        target_id=learning_package_id,
        user_id=user_id,
    )
    import_from_modulestore.save()
    save_legacy_content_to_staged_content_task.delay(import_from_modulestore.uuid)
    return import_from_modulestore

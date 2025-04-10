"""
API for course to library import.
"""
from functools import partial

from django.db import transaction

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
    import_course_staged_content_to_library_task.apply_async(
        kwargs={
            'usage_ids': usage_ids,
            'import_uuid': import_uuid,
            'user_id': user_id,
            'composition_level': composition_level,
            'override': override,
        },
    )


def create_import(source_key, user_id: int, learning_package_id: int) -> _Import:
    """
    Create a new import task to import a course to a library.
    """
    with transaction.atomic():
        import_from_modulestore = _Import.objects.create(
            source_key=source_key,
            target_id=learning_package_id,
            user_id=user_id,
        )
        transaction.on_commit(
            partial(save_legacy_content_to_staged_content_task.delay, import_uuid=str(import_from_modulestore.uuid))
        )
        return import_from_modulestore

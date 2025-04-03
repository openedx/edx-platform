"""
Tasks for course to library import.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from edx_django_utils.monitoring import set_code_owner_attribute

from openedx.core.djangoapps.content_staging import api as content_staging_api

from .constants import IMPORT_FROM_MODULESTORE_PURPOSE
from .helpers import get_items_to_import, ImportClient
from .models import Import, StagedContentForImport
from .validators import validate_composition_level

log = get_task_logger(__name__)


@shared_task
@set_code_owner_attribute
def save_courses_to_staged_content_task(import_uuid: str) -> None:
    """
    Save courses to staged content task.
    """
    import_event = Import.get_by_uuid(import_uuid)
    if not import_event:
        return

    import_event.clean_related_staged_content()
    try:
        with transaction.atomic():
            items_to_import = get_items_to_import(import_event)
            for item in items_to_import:
                staged_content = content_staging_api.stage_xblock_temporarily(
                    item,
                    import_event.user.id,
                    purpose=IMPORT_FROM_MODULESTORE_PURPOSE,
                )
                StagedContentForImport.objects.create(
                    staged_content=staged_content,
                    import_event=import_event
                )

            if items_to_import:
                import_event.ready()
            else:
                import_event.error()
    except Exception as exc:  # pylint: disable=broad-except
        import_event.error()
        raise exc


@shared_task
@set_code_owner_attribute
def import_course_staged_content_to_library_task(
    usage_ids: list[str],
    import_uuid: str,
    user_id: int,
    composition_level: str,
    override: bool
) -> None:
    """
    Import staged content to a library task.
    """
    validate_composition_level(composition_level)
    import_event = Import.get_ready_by_uuid(import_uuid)
    if not import_event or import_event.user_id != user_id:
        log.info('Ready import from modulestore not found')
        return

    with transaction.atomic():
        for usage_id in usage_ids:
            if staged_content_item := import_event.get_staged_content_by_block_usage_id(usage_id):
                import_client = ImportClient(
                    import_event,
                    usage_id,
                    staged_content_item,
                    composition_level,
                    override,
                )
                import_client.import_from_staged_content()

        import_event.imported()

"""
Tasks for course to library import.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from edx_django_utils.monitoring import set_code_owner_attribute

from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import LearningPackage
from openedx.core.djangoapps.content_staging import api as content_staging_api

from .constants import IMPORT_FROM_MODULESTORE_STAGING_PURPOSE
from .data import ImportStatus
from .helpers import get_items_to_import, import_from_staged_content
from .models import Import, PublishableEntityImport, StagedContentForImport
from .validators import validate_composition_level

log = get_task_logger(__name__)


@shared_task
@set_code_owner_attribute
def save_legacy_content_to_staged_content_task(import_uuid: str) -> None:
    """
    Save courses to staged content task by sections/chapters.
    """
    import_event = Import.objects.get(uuid=import_uuid)

    import_event.clean_related_staged_content()
    import_event.set_status(ImportStatus.STAGING)
    try:
        with transaction.atomic():
            items_to_import = get_items_to_import(import_event)
            for item in items_to_import:
                staged_content = content_staging_api.stage_xblock_temporarily(
                    item,
                    import_event.user.id,
                    purpose=IMPORT_FROM_MODULESTORE_STAGING_PURPOSE,
                )
                StagedContentForImport.objects.create(
                    staged_content=staged_content,
                    import_event=import_event,
                    source_usage_key=item.location
                )

            if items_to_import:
                import_event.set_status(ImportStatus.STAGED)
            else:
                import_event.set_status(ImportStatus.STAGING_FAILED)
    except Exception as exc:  # pylint: disable=broad-except
        import_event.set_status(ImportStatus.STAGING_FAILED)
        raise exc


@shared_task
@set_code_owner_attribute
def import_staged_content_to_library_task(
    usage_key_strings: list[str],
    import_uuid: str,
    learning_package_id: int,
    user_id: int,
    composition_level: str,
    override: bool,
) -> None:
    """
    Import staged content to a library task.
    """
    validate_composition_level(composition_level)

    import_event = Import.objects.get(uuid=import_uuid, status=ImportStatus.STAGED, user_id=user_id)
    target_learning_package = LearningPackage.objects.get(id=learning_package_id)

    imported_publishable_versions = []
    with authoring_api.bulk_draft_changes_for(learning_package_id=learning_package_id) as change_log:
        try:
            for usage_key_string in usage_key_strings:
                staged_content_for_import = import_event.staged_content_for_import.get(
                    source_usage_key=usage_key_string
                )
                publishable_versions = import_from_staged_content(
                    import_event,
                    usage_key_string,
                    target_learning_package,
                    staged_content_for_import.staged_content,
                    composition_level,
                    override,
                )
                imported_publishable_versions.extend(publishable_versions)
        except:  # pylint: disable=bare-except
            import_event.set_status(ImportStatus.IMPORTING_FAILED)
            raise

    import_event.set_status(ImportStatus.IMPORTED)
    for imported_component_version in imported_publishable_versions:
        PublishableEntityImport.objects.create(
            import_event=import_event,
            resulting_mapping=imported_component_version.mapping,
            resulting_change=change_log.records.get(entity=imported_component_version.mapping.target_entity),
        )

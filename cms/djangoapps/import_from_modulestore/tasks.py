"""
Tasks for course to library import.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocatorV2
from user_tasks.tasks import UserTask

from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import LearningPackage
from openedx.core.djangoapps.content_staging import api as content_staging_api
from openedx.core.djangoapps.content_libraries.api import ContainerType
from xmodule.modulestore.exceptions import ItemNotFoundError

from .constants import IMPORT_FROM_MODULESTORE_STAGING_PURPOSE
from .helpers import get_items_to_import, ImportClient
from .models import (
    Import, PublishableEntityImport, StagedContentForImport,
    COMPOSITION_LEVEL_COMPONENT,
)

log = get_task_logger(__name__)


class ImportTask(UserTask):
    pass


@shared_task(base=ImportTask, bind=True)
def import_legacy_content(
    self: ImportTask,
    user_id: int,
    *,
    source_key: str,
    target_key: str,
    override: bool,
    composition_level: str,
) -> None:
    import_event = Import.objects.create(
        user_task_status=self.status,
        source_key=CourseKey.from_string(source_key),
        target_key=LibraryLocatorV2.from_string(target_key),
        override=override,
        composition_level=composition_level,
    )
    import_event.set_state(f"Preparing to stage content")
    import_event.clean_related_staged_content()
    target_package = authoring_api.get_learning_package_by_key(target_key)
    items_to_import: list['XBlock'] = get_items_to_import(import_event)
    if not items_to_import:
        import_event.fail("Nothing to stage for import")
        return
    for item in items_to_import:
        import_event.set_state(f"Staging content: {item.usage_key}")
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
    import_event.set_state(f"Content is staged, preparing to import")
    with authoring_api.bulk_draft_changes_for(learning_package_id=learning_package_id) as change_log:
        for staged_content_item in import_event.staged_content_for_import:
            source_key = staged_content_item.source_usage_key
            import_event.set_state(f"Importing staged content: {source_key}")
            import_client = ImportClient(
                import_event=import_event,
                usage_key_string=source_key,
                target_learning_package=target_package,
                staged_content=staged_content_item.staged_content,
                composition_level=(
                    None
                    if composition_level == COMPOSITION_LEVEL_COMPONENT
                    else ContainerType(composition_level)
                ),
                override=override,
            )
            imported_publishable_versions.extend(import_client.import_from_staged_content())
    import_event.set_state(f"Finalizing import")
    for imported_component_version in imported_publishable_versions:
        PublishableEntityImport.objects.create(
            import_event=import_event,
            resulting_mapping=imported_component_version.mapping,
            resulting_change=change_log.records.get(entity=imported_component_version.mapping.target_entity),
        )

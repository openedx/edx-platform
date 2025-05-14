"""
Tasks for course to library import.
"""
from typing import Sequence

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from edx_django_utils.monitoring import set_code_owner_attribute_from_module
from opaque_keys.edx.keys import UsageKey

from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import LearningPackage
from openedx.core.djangoapps.content_staging import api as content_staging_api
from user_tasks.tasks import UserTask

from .constants import IMPORT_FROM_MODULESTORE_STAGING_PURPOSE
from .data import ImportStatus
from .helpers import get_items_to_import, import_from_staged_content
from .models import Import, PublishableEntityImport, StagedContentForImport

log = get_task_logger(__name__)


class ImportToLibraryTask(UserTask):
    """
    Base class for import to library tasks.
    """

    @staticmethod
    def calculate_total_steps(arguments_dict):
        """
        Get number of in-progress steps in importing process, as shown in the UI.

        For reference, these are:

        1. Staging content
        2. Importing staged content into library
        """
        return 2

    @classmethod
    def generate_name(cls, arguments_dict):
        """
        Create a name for this particular import task instance.

        Arguments:
            arguments_dict (dict): The arguments given to the task function

        Returns:
            str: The generated name
        """
        library_id = arguments_dict.get('learning_package_id')
        import_id = arguments_dict.get('import_pk')
        return f'Import course to library (library_id={library_id}, import_id={import_id})'


@shared_task(base=ImportToLibraryTask, bind=True)
# Note: The decorator @set_code_owner_attribute cannot be used here because the UserTaskMixin
#   does stack inspection and can't handle additional decorators.
def import_to_library_task(
    self,
    import_pk: int,
    usage_key_strings: Sequence[str | UsageKey],
    learning_package_id: int,
    user_id: int,
) -> None:
    """
    Import to library task.

    1. Save course (for now) to staged content task by sections/chapters.
    2. Import staged content to library task.
    """
    set_code_owner_attribute_from_module(__name__)

    # Step 1: Save course to staged content task by sections/chapters.
    try:
        import_event = Import.objects.get(pk=import_pk)
        import_event.user_task_status = self.status
        import_event.save(update_fields=['user_task_status'])
    except Import.DoesNotExist:
        log.info('Import event not found for pk %s', import_pk)
        return

    import_event.set_status(ImportStatus.WAITNG_TO_STAGE)
    import_event.clean_related_staged_content()

    import_event.set_status(ImportStatus.STAGING)
    try:
        with transaction.atomic():
            items_to_import = get_items_to_import(import_event)
            for item in items_to_import:
                staged_content = content_staging_api.stage_xblock_temporarily(
                    item,
                    user_id,
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

    # Step 2: Import staged content to library task.
    self.status.increment_completed_steps()

    target_learning_package = LearningPackage.objects.get(id=learning_package_id)

    imported_publishable_versions = []
    import_event.set_status(ImportStatus.IMPORTING)
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
                    import_event.composition_level,
                    import_event.override,
                )
                imported_publishable_versions.extend(publishable_versions)
        except Exception as exc:  # pylint: disable=broad-except
            import_event.set_status(ImportStatus.IMPORTING_FAILED)
            raise exc
        else:
            import_event.set_status(ImportStatus.IMPORTED)
            for imported_component_version in imported_publishable_versions:
                PublishableEntityImport.objects.create(
                    import_event=import_event,
                    resulting_mapping=imported_component_version.mapping,
                    resulting_change=change_log.records.get(entity=imported_component_version.mapping.target_entity),
                )
        finally:
            import_event.clean_related_staged_content()

"""
Celery tasks for Content Libraries.

Architecture note:

    Several functions in this file manage the copying/updating of blocks in modulestore
    and learning core. These operations should only be performed within the context of CMS.
    However, due to existing edx-platform code structure, we've had to define the functions
    in shared source tree (openedx/) and the tasks are registered in both LMS and CMS.

    To ensure that we're not accidentally importing things from learning core in the LMS context,
    we use ensure_cms throughout this module.

    A longer-term solution to this issue would be to move the content_libraries app to cms:
    https://github.com/openedx/edx-platform/issues/33428
"""
from __future__ import annotations

import logging

from celery import shared_task
from celery_utils.logged_task import LoggedTask
from celery.utils.log import get_task_logger
from edx_django_utils.monitoring import set_code_owner_attribute, set_code_owner_attribute_from_module

from user_tasks.tasks import UserTask, UserTaskStatus
from xblock.fields import Scope

from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator
from openedx.core.lib import ensure_cms
from xmodule.capa_block import ProblemBlock
from xmodule.library_content_block import ANY_CAPA_TYPE_VALUE, LegacyLibraryContentBlock
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.mixed import MixedModuleStore

from . import api
from .models import ContentLibraryBlockImportTask

logger = logging.getLogger(__name__)
TASK_LOGGER = get_task_logger(__name__)


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def import_blocks_from_course(import_task_id, course_key_str, use_course_key_as_block_id_suffix=True):
    """
    A Celery task to import blocks from a course through modulestore.
    """
    ensure_cms("import_blocks_from_course may only be executed in a CMS context")

    course_key = CourseKey.from_string(course_key_str)

    with ContentLibraryBlockImportTask.execute(import_task_id) as import_task:

        def on_progress(block_key, block_num, block_count, exception=None):
            if exception:
                logger.exception('Import block failed: %s', block_key)
            else:
                logger.info('Import block succesful: %s', block_key)
            import_task.save_progress(block_num / block_count)

        edx_client = api.EdxModulestoreImportClient(
            library=import_task.library,
            use_course_key_as_block_id_suffix=use_course_key_as_block_id_suffix
        )
        edx_client.import_blocks_from_course(
            course_key, on_progress
        )


def _filter_child(store, usage_key, capa_type):
    """
    Return whether this block is both a problem and has a `capa_type` which is included in the filter.
    """
    if usage_key.block_type != "problem":
        return False

    descriptor = store.get_item(usage_key, depth=0)
    assert isinstance(descriptor, ProblemBlock)
    return capa_type in descriptor.problem_types


def _problem_type_filter(store, library, capa_type):
    """ Filters library children by capa type."""
    return [key for key in library.children if _filter_child(store, key, capa_type)]


class LibrarySyncChildrenTask(UserTask):  # pylint: disable=abstract-method
    """
    Base class for tasks which operate upon library_content children.
    """

    @classmethod
    def generate_name(cls, arguments_dict) -> str:
        """
        Create a name for this particular import task instance.

        Should be both:
        a. semi human-friendly
        b. something we can query in order to determine whether the dest block has a task in progress

        Arguments:
            arguments_dict (dict): The arguments given to the task function
        """
        key = arguments_dict['dest_block_id']
        return f'Updating {key} from library'


# Note: The decorator @set_code_owner_attribute cannot be used here because the UserTaskMixin does stack
# inspection and can't handle additional decorators. So, wet set the code_owner attribute in the tasks' bodies instead.

@shared_task(base=LibrarySyncChildrenTask, bind=True)
def sync_from_library(
    self: LibrarySyncChildrenTask,
    user_id: int,
    dest_block_id: str,
    library_version: str | None,
) -> None:
    """
    Celery task to update the children of the library_content block at `dest_block_id`.
    """
    set_code_owner_attribute_from_module(__name__)
    store = modulestore()
    dest_block = store.get_item(BlockUsageLocator.from_string(dest_block_id))
    _sync_children(
        task=self,
        store=store,
        user_id=user_id,
        dest_block=dest_block,
        library_version=library_version,
    )


@shared_task(base=LibrarySyncChildrenTask, bind=True)
def duplicate_children(
    self: LibrarySyncChildrenTask,
    user_id: int,
    source_block_id: str,
    dest_block_id: str,
) -> None:
    """
    Celery task to duplicate the children from `source_block_id` to `dest_block_id`.
    """
    set_code_owner_attribute_from_module(__name__)
    store = modulestore()
    # First, populate the destination block with children imported from the library.
    # It's important that _sync_children does this at the currently-set version of the dest library
    # (someone may be duplicating an out-of-date block).
    dest_block = store.get_item(BlockUsageLocator.from_string(dest_block_id))
    _sync_children(
        task=self,
        store=store,
        user_id=user_id,
        dest_block=dest_block,
        library_version=dest_block.source_library_version,
    )
    # Then, copy over any overridden settings the course author may have applied to the blocks.
    source_block = store.get_item(BlockUsageLocator.from_string(source_block_id))
    with store.bulk_operations(source_block.scope_ids.usage_id.context_key):
        try:
            TASK_LOGGER.info('Copying Overrides from %s to %s', source_block_id, dest_block_id)
            _copy_overrides(store=store, user_id=user_id, source_block=source_block, dest_block=dest_block)
        except Exception as exception:  # pylint: disable=broad-except
            TASK_LOGGER.exception('Error Copying Overrides from %s to %s', source_block_id, dest_block_id)
            if self.status.state != UserTaskStatus.FAILED:
                self.status.fail({'raw_error_msg': str(exception)})


def _sync_children(
    task: LibrarySyncChildrenTask,
    store: MixedModuleStore,
    user_id: int,
    dest_block: LegacyLibraryContentBlock,
    library_version: str | None,
) -> None:
    """
    Implementation helper for `sync_from_library` and `duplicate_children` Celery tasks.

    Can update children with a specific library `library_version`, or latest (`library_version=None`).
    """
    source_blocks = []
    library_key = dest_block.source_library_key.for_branch(
        ModuleStoreEnum.BranchName.library
    ).for_version(library_version)
    try:
        library = store.get_library(library_key, remove_version=False, remove_branch=False, head_validation=False)
    except ItemNotFoundError:
        task.status.fail(f"Requested library {library_key} not found.")
        return
    filter_children = (dest_block.capa_type != ANY_CAPA_TYPE_VALUE)
    if filter_children:
        # Apply simple filtering based on CAPA problem types:
        source_blocks.extend(_problem_type_filter(store, library, dest_block.capa_type))
    else:
        source_blocks.extend(library.children)
    with store.bulk_operations(dest_block.scope_ids.usage_id.context_key):
        try:
            dest_block.source_library_version = str(library.location.library_key.version_guid)
            store.update_item(dest_block, user_id)
            dest_block.children = store.copy_from_template(
                source_blocks, dest_block.location, user_id, head_validation=True
            )
            # ^-- copy_from_template updates the children in the DB
            # but we must also set .children here to avoid overwriting the DB again
        except Exception as exception:  # pylint: disable=broad-except
            TASK_LOGGER.exception('Error importing children for %s', dest_block.scope_ids.usage_id, exc_info=True)
            if task.status.state != UserTaskStatus.FAILED:
                task.status.fail({'raw_error_msg': str(exception)})
            raise


def _copy_overrides(
    store: MixedModuleStore,
    user_id: int,
    source_block: LegacyLibraryContentBlock,
    dest_block: LegacyLibraryContentBlock
) -> None:
    """
    Copy any overrides the user has made on children of `source` over to the children of `dest_block`, recursively.
    """
    for field in source_block.fields.values():
        if field.scope == Scope.settings and field.is_set_on(source_block):
            setattr(dest_block, field.name, field.read_from(source_block))
    if source_block.has_children:
        for source_child_key, dest_child_key in zip(source_block.children, dest_block.children):
            _copy_overrides(
                store=store,
                user_id=user_id,
                source_block=store.get_item(source_child_key),
                dest_block=store.get_item(dest_child_key),
            )
    store.update_item(dest_block, user_id)

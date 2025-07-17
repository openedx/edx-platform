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
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import (
    BlockUsageLocator,
    LibraryCollectionLocator,
    LibraryContainerLocator,
    LibraryLocatorV2,
)
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import DraftChangeLog, PublishLog
from openedx_events.content_authoring.data import (
    LibraryBlockData,
    LibraryCollectionData,
    LibraryContainerData,
)
from openedx_events.content_authoring.signals import (
    LIBRARY_BLOCK_CREATED,
    LIBRARY_BLOCK_DELETED,
    LIBRARY_BLOCK_UPDATED,
    LIBRARY_BLOCK_PUBLISHED,
    LIBRARY_COLLECTION_UPDATED,
    LIBRARY_CONTAINER_CREATED,
    LIBRARY_CONTAINER_DELETED,
    LIBRARY_CONTAINER_UPDATED,
    LIBRARY_CONTAINER_PUBLISHED,
)

from user_tasks.tasks import UserTask, UserTaskStatus
from xblock.fields import Scope

from openedx.core.lib import ensure_cms
from xmodule.capa_block import ProblemBlock
from xmodule.library_content_block import ANY_CAPA_TYPE_VALUE, LegacyLibraryContentBlock
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.mixed import MixedModuleStore

from . import api
from .models import ContentLibraryBlockImportTask

log = logging.getLogger(__name__)
TASK_LOGGER = get_task_logger(__name__)


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def send_events_after_publish(publish_log_pk: int, library_key_str: str) -> None:
    """
    Send events to trigger actions like updating the search index, after we've
    published some items in a library.

    We use the PublishLog record so we can detect exactly what was changed,
    including any auto-published changes like child items in containers.

    This happens in a celery task so that it can be run asynchronously if
    needed, because the "publish all changes" action can potentially publish
    hundreds or even thousands of components/containers at once, and synchronous
    event handlers like updating the search index may a while to complete in
    that case.
    """
    publish_log = PublishLog.objects.get(pk=publish_log_pk)
    library_key = LibraryLocatorV2.from_string(library_key_str)
    affected_entities = publish_log.records.select_related("entity", "entity__container", "entity__component").all()
    affected_containers: set[LibraryContainerLocator] = set()

    # Update anything that needs to be updated (e.g. search index):
    for record in affected_entities:
        if hasattr(record.entity, "component"):
            usage_key = api.library_component_usage_key(library_key, record.entity.component)
            # Note that this item may be newly created, updated, or even deleted - but all we care about for this event
            # is that the published version is now different. Only for draft changes do we send differentiated events.
            LIBRARY_BLOCK_PUBLISHED.send_event(
                library_block=LibraryBlockData(library_key=library_key, usage_key=usage_key)
            )
            # Publishing a container will auto-publish its children, but publishing a single component or all changes
            # in the library will NOT usually include any parent containers. But we do need to notify listeners that the
            # parent container(s) have changed, e.g. so the search index can update the "has_unpublished_changes"
            for parent_container in api.get_containers_contains_item(usage_key):
                affected_containers.add(parent_container.container_key)
                # TODO: should this be a CONTAINER_CHILD_PUBLISHED event instead of CONTAINER_PUBLISHED ?
        elif hasattr(record.entity, "container"):
            container_key = api.library_container_locator(library_key, record.entity.container)
            affected_containers.add(container_key)
        else:
            log.warning(
                f"PublishableEntity {record.entity.pk} / {record.entity.key} was modified during publish operation "
                "but is of unknown type."
            )

    for container_key in affected_containers:
        LIBRARY_CONTAINER_PUBLISHED.send_event(
            library_container=LibraryContainerData(container_key=container_key)
        )


def wait_for_post_publish_events(publish_log: PublishLog, library_key: LibraryLocatorV2):
    """
    After publishing some changes, trigger the required event handlers (e.g.
    update the search index). Try to wait for that to complete before returning,
    up to some reasonable timeout, and then finish anything remaining
    asynchonrously.
    """
    # Update the search index (and anything else) for the affected blocks
    result = send_events_after_publish.apply_async(args=(publish_log.pk, str(library_key)))
    # Try waiting a bit for those post-publish events to be handled:
    try:
        result.get(timeout=15)
    except TimeoutError:
        pass
        # This is fine! The search index is still being updated, and/or other
        # event handlers are still following up on the results, but the publish
        # already *did* succeed, and the events will continue to be processed in
        # the background by the celery worker until everything is updated.


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def send_events_after_revert(draft_change_log_id: int, library_key_str: str) -> None:
    """
    Send events to trigger actions like updating the search index, after we've
    reverted some unpublished changes in a library.

    See notes on the analogous function above, send_events_after_publish.
    """
    try:
        draft_change_log = DraftChangeLog.objects.get(id=draft_change_log_id)
    except DraftChangeLog.DoesNotExist:
        # When a revert operation is a no-op, Learning Core deletes the empty
        # DraftChangeLog, so we'll assume that's what happened here.
        log.info(f"Library revert in {library_key_str} did not result in any changes.")
        return

    library_key = LibraryLocatorV2.from_string(library_key_str)
    affected_entities = draft_change_log.records.select_related(
        "entity", "entity__container", "entity__component",
    ).all()

    created_container_keys: set[LibraryContainerLocator] = set()
    updated_container_keys: set[LibraryContainerLocator] = set()
    deleted_container_keys: set[LibraryContainerLocator] = set()
    affected_collection_keys: set[LibraryCollectionLocator] = set()

    # Update anything that needs to be updated (e.g. search index):
    for record in affected_entities:
        # This will be true if the entity was [soft] deleted, but we're now reverting that deletion:
        is_undeleted = (record.old_version is None and record.new_version is not None)
        # This will be true if the entity was created and we're now deleting it by reverting that creation:
        is_deleted = (record.old_version is not None and record.new_version is None)
        if hasattr(record.entity, "component"):
            usage_key = api.library_component_usage_key(library_key, record.entity.component)
            event = LIBRARY_BLOCK_UPDATED
            if is_deleted:
                event = LIBRARY_BLOCK_DELETED
            elif is_undeleted:
                event = LIBRARY_BLOCK_CREATED
            event.send_event(library_block=LibraryBlockData(library_key=library_key, usage_key=usage_key))
            # If any containers contain this component, their child list / component count may need to be updated
            # e.g. if this was a newly created component in the container and is now deleted, or this was deleted and
            # is now restored.
            for parent_container in api.get_containers_contains_item(usage_key):
                updated_container_keys.add(parent_container.container_key)

            # TODO: do we also need to send CONTENT_OBJECT_ASSOCIATIONS_CHANGED for this component, or is
            # LIBRARY_BLOCK_UPDATED sufficient?
        elif hasattr(record.entity, "container"):
            container_key = api.library_container_locator(library_key, record.entity.container)
            if is_deleted:
                deleted_container_keys.add(container_key)
            elif is_undeleted:
                created_container_keys.add(container_key)
            else:
                updated_container_keys.add(container_key)
        else:
            log.warning(
                f"PublishableEntity {record.entity.pk} / {record.entity.key} was modified during publish operation "
                "but is of unknown type."
            )
        # If any collections contain this entity, their item count may need to be updated, e.g. if this was a
        # newly created component in the collection and is now deleted, or this was deleted and is now re-added.
        for parent_collection in authoring_api.get_entity_collections(
            record.entity.learning_package_id, record.entity.key,
        ):
            collection_key = api.library_collection_locator(
                library_key=library_key,
                collection_key=parent_collection.key,
            )
            affected_collection_keys.add(collection_key)

    for container_key in deleted_container_keys:
        LIBRARY_CONTAINER_DELETED.send_event(
            library_container=LibraryContainerData(container_key=container_key)
        )
        # Don't bother sending UPDATED events for these containers that are now deleted
        created_container_keys.discard(container_key)

    for container_key in created_container_keys:
        LIBRARY_CONTAINER_CREATED.send_event(
            library_container=LibraryContainerData(container_key=container_key)
        )

    for container_key in updated_container_keys:
        LIBRARY_CONTAINER_UPDATED.send_event(
            library_container=LibraryContainerData(container_key=container_key)
        )

    for collection_key in affected_collection_keys:
        LIBRARY_COLLECTION_UPDATED.send_event(
            library_collection=LibraryCollectionData(collection_key=collection_key)
        )


def wait_for_post_revert_events(draft_change_log: DraftChangeLog, library_key: LibraryLocatorV2):
    """
    After discard all changes in a library, trigger the required event handlers
    (e.g. update the search index). Try to wait for that to complete before
    returning, up to some reasonable timeout, and then finish anything remaining
    asynchonrously.
    """
    # Update the search index (and anything else) for the affected blocks
    result = send_events_after_revert.apply_async(args=(draft_change_log.pk, str(library_key)))
    # Try waiting a bit for those post-publish events to be handled:
    try:
        result.get(timeout=15)
    except TimeoutError:
        pass
        # This is fine! The search index is still being updated, and/or other
        # event handlers are still following up on the results, but the revert
        # already *did* succeed, and the events will continue to be processed in
        # the background by the celery worker until everything is updated.


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
                log.exception('Import block failed: %s', block_key)
            else:
                log.info('Import block succesful: %s', block_key)
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

    FIXME: this is related to legacy modulestore libraries and shouldn't be part of the
    openedx.core.djangoapps.content_libraries app, which is the app for v2 libraries.
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

    FIXME: this is related to legacy modulestore libraries and shouldn't be part of the
    openedx.core.djangoapps.content_libraries app, which is the app for v2 libraries.
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

    FIXME: this is related to legacy modulestore libraries and shouldn't be part of the
    openedx.core.djangoapps.content_libraries app, which is the app for v2 libraries.
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

    FIXME: this is related to legacy modulestore libraries and shouldn't be part of the
    openedx.core.djangoapps.content_libraries app, which is the app for v2 libraries.
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

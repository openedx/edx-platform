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
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import PermissionDenied
from edx_django_utils.monitoring import set_code_owner_attribute, set_code_owner_attribute_from_module
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import (
    BlockUsageLocator,
    LibraryLocatorV2,
    LibraryUsageLocatorV2,
    LibraryLocator as LibraryLocatorV1
)

from user_tasks.tasks import UserTask, UserTaskStatus
from xblock.fields import Scope

from common.djangoapps.student.auth import has_studio_write_access
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content_libraries import api as library_api
from openedx.core.djangoapps.xblock.api import load_block
from openedx.core.lib import ensure_cms
from xmodule.capa_block import ProblemBlock
from xmodule.library_content_block import ANY_CAPA_TYPE_VALUE, LibraryContentBlock
from xmodule.library_root_xblock import LibraryRoot as LibraryRootV1
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.mixed import MixedModuleStore
from xmodule.modulestore.split_mongo import BlockKey
from xmodule.util.keys import derive_key

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


def _import_block(store, user_id, source_block, dest_parent_key):
    """
    Recursively import a learning core block and its children.`
    """
    def generate_block_key(source_key, dest_parent_key):
        """
        Deterministically generate an ID for the new block and return the key.
        Keys are generated such that they appear identical to a v1 library with
        the same input block_id, library name, library organization, and parent block using derive_key
        """
        if not isinstance(source_key.lib_key, LibraryLocatorV2):
            raise TypeError(f"Expected source library key of type LibraryLocatorV2, got {source_key.lib_key} instead.")
        source_key_as_v1_course_key = LibraryLocatorV1(
            org=source_key.lib_key.org,
            library=source_key.lib_key.slug,
            branch='library'
        )
        derived_block_key = derive_key(
            source=source_key_as_v1_course_key.make_usage_key(source_key.block_type, source_key.block_id),
            dest_parent=BlockKey(dest_parent_key.block_type, dest_parent_key.block_id),
        )
        return dest_parent_key.context_key.make_usage_key(*derived_block_key)

    source_key = source_block.scope_ids.usage_id
    new_block_key = generate_block_key(source_key, dest_parent_key)
    try:
        new_block = store.get_item(new_block_key)
        if new_block.parent.block_id != dest_parent_key.block_id:
            raise ValueError(
                "Expected existing block {} to be a child of {} but instead it's a child of {}".format(
                    new_block_key, dest_parent_key, new_block.parent,
                )
            )
    except ItemNotFoundError:
        new_block = store.create_child(
            user_id,
            dest_parent_key,
            source_key.block_type,
            block_id=new_block_key.block_id,
        )

    # Prepare a list of this block's static assets; any assets that are referenced as /static/{path} (the
    # recommended way for referencing them) will stop working, and so we rewrite the url when importing.
    # Copying assets not advised because modulestore doesn't namespace assets to each block like learning core, which
    # might cause conflicts when the same filename is used across imported blocks.
    if isinstance(source_key, LibraryUsageLocatorV2):
        all_assets = library_api.get_library_block_static_asset_files(source_key)
    else:
        all_assets = []

    for field_name, field in source_block.fields.items():
        if field.scope not in (Scope.settings, Scope.content):
            continue  # Only copy authored field data
        if field.is_set_on(source_block) or field.is_set_on(new_block):
            field_value = getattr(source_block, field_name)
            setattr(new_block, field_name, field_value)
    new_block.save()
    store.update_item(new_block, user_id)

    if new_block.has_children:
        # Delete existing children in the new block, which can be reimported again if they still exist in the
        # source library
        for existing_child_key in new_block.children:
            store.delete_item(existing_child_key, user_id)
        # Now import the children
        for child in source_block.get_children():
            _import_block(store, user_id, child, new_block_key)

    return new_block_key


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


def _import_from_learning_core(user_id, store, dest_block, source_block_ids):
    """
    Imports a block from a learning-core-based learning context (usually a
    content library) into modulestore, as a new child of dest_block.
    Any existing children of dest_block are replaced.
    """
    dest_key = dest_block.scope_ids.usage_id
    if not isinstance(dest_key, BlockUsageLocator):
        raise TypeError(f"Destination {dest_key} should be a modulestore course.")
    if user_id is None:
        raise ValueError("Cannot check user permissions - LibraryTools user_id is None")

    if len(set(source_block_ids)) != len(source_block_ids):
        # We don't support importing the exact same block twice because it would break the way we generate new IDs
        # for each block and then overwrite existing copies of blocks when re-importing the same blocks.
        raise ValueError("One or more library component IDs is a duplicate.")

    dest_course_key = dest_key.context_key
    user = User.objects.get(id=user_id)
    if not has_studio_write_access(user, dest_course_key):
        raise PermissionDenied()

    # Read the source block; this will also confirm that user has permission to read it.
    # (This could be slow and use lots of memory, except for the fact that LibraryContentBlock which calls this
    # should be limiting the number of blocks to a reasonable limit. We load them all now instead of one at a
    # time in order to raise any errors before we start actually copying blocks over.)
    orig_blocks = [load_block(UsageKey.from_string(key), user) for key in source_block_ids]

    with store.bulk_operations(dest_course_key):
        child_ids_updated = set()

        for block in orig_blocks:
            new_block_id = _import_block(store, user_id, block, dest_key)
            child_ids_updated.add(new_block_id)

        # Remove any existing children that are no longer used
        for old_child_id in set(dest_block.children) - child_ids_updated:
            store.delete_item(old_child_id, user_id)
        # If this was called from a handler, it will save dest_block at the end, so we must update
        # dest_block.children to avoid it saving the old value of children and deleting the new ones.
        dest_block.children = store.get_item(dest_key).children


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
    library_version: str | int | None,
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
    dest_block: LibraryContentBlock,
    library_version: int | str | None,
) -> None:
    """
    Implementation helper for `sync_from_library` and `duplicate_children` Celery tasks.

    Can update children with a specific library `library_version`, or latest (`library_version=None`).
    """
    source_blocks = []
    library_key = dest_block.source_library_key
    filter_children = (dest_block.capa_type != ANY_CAPA_TYPE_VALUE)
    library = library_api.get_v1_or_v2_library(library_key, version=library_version)
    if not library:
        task.status.fail(f"Requested library {library_key} not found.")
    elif isinstance(library, LibraryRootV1):
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
    elif isinstance(library, library_api.ContentLibraryMetadata):
        # TODO: add filtering by capa_type when V2 library will support different problem types
        try:
            source_block_ids = [
                str(library_api.LibraryXBlockMetadata.from_component(library_key, component).usage_key)
                for component in library_api.get_library_components(library_key)
            ]
            _import_from_learning_core(user_id, store, dest_block, source_block_ids)
            dest_block.source_library_version = str(library.version)
            store.update_item(dest_block, user_id)
        except Exception as exception:  # pylint: disable=broad-except
            TASK_LOGGER.exception('Error importing children for %s', dest_block.scope_ids.usage_id, exc_info=True)
            if task.status.state != UserTaskStatus.FAILED:
                task.status.fail({'raw_error_msg': str(exception)})
            raise


def _copy_overrides(
    store: MixedModuleStore,
    user_id: int,
    source_block: LibraryContentBlock,
    dest_block: LibraryContentBlock
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

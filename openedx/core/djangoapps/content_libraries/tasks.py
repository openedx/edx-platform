"""
Celery tasks for Content Libraries.

Architecture note:

    Several functions in this file manage the copying/updating of blocks in modulestore
    and blockstore. These operations should only be performed within the context of CMS.
    However, due to existing edx-platform code structure, we've had to define the functions
    in shared source tree (openedx/) and the tasks are registered in both LMS and CMS.

    To ensure that we're not accidentally importing things from blockstore in the LMS context,
    we use ensure_cms throughout this module.

    A longer-term solution to this issue would be to move the content_libraries app to cms:
    https://github.com/openedx/edx-platform/issues/33428
"""

import logging
import hashlib

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
    LibraryUsageLocator,
    LibraryUsageLocatorV2
)
from search.search_engine_base import SearchEngine

from user_tasks.tasks import UserTask, UserTaskStatus
from xblock.fields import Scope

from common.djangoapps.student.auth import has_studio_write_access
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content_libraries import api as library_api
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.djangoapps.xblock.api import load_block
from openedx.core.lib import ensure_cms, blockstore_api
from xmodule.capa_block import ProblemBlock
from xmodule.library_content_block import ANY_CAPA_TYPE_VALUE
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from . import api
from .models import ContentLibraryBlockImportTask

logger = logging.getLogger(__name__)
TASK_LOGGER = get_task_logger(__name__)


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def import_blocks_from_course(import_task_id, course_key_str):
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

        edx_client = api.EdxModulestoreImportClient(library=import_task.library)
        edx_client.import_blocks_from_course(
            course_key, on_progress
        )


def normalize_key_for_search(library_key):
    """ Normalizes library key for use with search indexing """
    return library_key.replace(version_guid=None, branch=None)


def _import_block(store, user_id, source_block, dest_parent_key):
    """
    Recursively import a blockstore block and its children. See import_from_blockstore.
    """
    def generate_block_key(source_key, dest_parent_key):
        """
        Deterministically generate an ID for the new block and return the key
        """
        block_id = (
            dest_parent_key.block_id[:10] +
            '-' +
            hashlib.sha1(str(source_key).encode('utf-8')).hexdigest()[:10]
        )
        return dest_parent_key.context_key.make_usage_key(source_key.block_type, block_id)

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
    # Copying assets not advised because modulestore doesn't namespace assets to each block like blockstore, which
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
            if isinstance(field_value, str):
                # If string field (which may also be JSON/XML data), rewrite /static/... URLs to point to blockstore
                for asset in all_assets:
                    field_value = field_value.replace(f'/static/{asset.path}', asset.url)
                    # Make sure the URL is one that will work from the user's browser when using the docker devstack
                    field_value = blockstore_api.force_browser_url(field_value)
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


def _get_library(store, library_key):
    """
    Helper method to get either V1 or V2 library.

    Given a library key like "library-v1:ProblemX+PR0B" (V1) or "lib:RG:rg-1" (v2), return the 'library'.

    is_v2_lib (bool) indicates which library storage should be requested:
        True - blockstore (V2 library);
        False - modulestore (V1 library).

    Returns None on error.
    """
    if isinstance(library_key, LibraryLocatorV2):
        try:
            return library_api.get_library(library_key)
        except ContentLibrary.DoesNotExist:
            return None
    else:
        try:
            return store.get_library(
                library_key, remove_version=False, remove_branch=False, head_validation=False
            )
        except ItemNotFoundError:
            return None


def _problem_type_filter(store, library, capa_type):
    """ Filters library children by capa type."""
    try:
        search_engine = SearchEngine.get_search_engine(index="library_index")
    except:  # pylint: disable=bare-except
        search_engine = None
    if search_engine:
        filter_clause = {
            "library": str(normalize_key_for_search(library.location.library_key)),
            "content_type": ProblemBlock.INDEX_CONTENT_TYPE,
            "problem_types": capa_type
        }
        search_result = search_engine.search(field_dictionary=filter_clause)
        results = search_result.get('results', [])
        return [LibraryUsageLocator.from_string(item['data']['id']) for item in results]
    else:
        return [key for key in library.children if _filter_child(store, key, capa_type)]


def import_from_blockstore(user_id, store, dest_block, blockstore_block_ids):
    """
    Imports a block from a blockstore-based learning context (usually a
    content library) into modulestore, as a new child of dest_block.
    Any existing children of dest_block are replaced.
    """
    ensure_cms("import_from_blockstore may only be executed in a CMS context")
    dest_key = dest_block.scope_ids.usage_id
    if not isinstance(dest_key, BlockUsageLocator):
        raise TypeError(f"Destination {dest_key} should be a modulestore course.")
    if user_id is None:
        raise ValueError("Cannot check user permissions - LibraryTools user_id is None")

    if len(set(blockstore_block_ids)) != len(blockstore_block_ids):
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
    orig_blocks = [load_block(UsageKey.from_string(key), user) for key in blockstore_block_ids]

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


class LibraryUpdateChildrenTask(UserTask):  # pylint: disable=abstract-method
    """
    Base class for course and library export tasks.
    """

    @staticmethod
    def calculate_total_steps(arguments_dict):
        """
        Get the number of in-progress steps in the export process, as shown in the UI.

        For reference, these are:

        1. Importing
        """
        return 1

    @classmethod
    def generate_name(cls, arguments_dict):
        """
        Create a name for this particular import task instance.

        Arguments:
            arguments_dict (dict): The arguments given to the task function

        Returns:
            text_type: The generated name
        """
        key = arguments_dict['dest_block_key']
        return f'Import of {key}'


@shared_task(base=LibraryUpdateChildrenTask, bind=True)
# Note: The decorator @set_code_owner_attribute cannot be used here because the UserTaskMixin
#       does stack inspection and can't handle additional decorators.
#       So, wet set the code_owner attribute in the task's body instead.
def update_children_task(self, user_id, dest_block_key, version=None):
    """
    Update xBlock's children.

    Re-fetch all matching blocks from the libraries, and copy them as children of dest_block.
    The children will be given new block_ids.

    This method will update dest_block's 'source_library_version' field to
    store the version number of the libraries used, so we easily determine
    if dest_block is up to date or not.
    """
    set_code_owner_attribute_from_module(__name__)
    ensure_cms("library_content block children may only be updated in a CMS context")
    store = modulestore()
    dest_block_id = BlockUsageLocator.from_string(dest_block_key)
    dest_block = store.get_item(dest_block_id)
    source_blocks = []
    library_key = dest_block.source_library_key
    is_v2_lib = isinstance(library_key, LibraryLocatorV2)

    if version and not is_v2_lib:
        library_key = library_key.replace(branch=ModuleStoreEnum.BranchName.library, version_guid=version)

    library = _get_library(store, library_key)
    if library is None:
        self.status.fail(f"Requested library {library_key} not found.")
        return

    if hasattr(dest_block, 'capa_type'):
        filter_children = (dest_block.capa_type != ANY_CAPA_TYPE_VALUE)
    else:
        filter_children = None
    if not is_v2_lib:
        if filter_children:
            # Apply simple filtering based on CAPA problem types:
            source_blocks.extend(_problem_type_filter(store, library, dest_block.capa_type))
        else:
            source_blocks.extend(library.children)
        with store.bulk_operations(dest_block.location.course_key):
            try:
                dest_block.source_library_version = str(library.location.library_key.version_guid)
                store.update_item(dest_block, user_id)
                head_validation = not version
                dest_block.children = store.copy_from_template(
                    source_blocks, dest_block.location, user_id, head_validation=head_validation
                )
                # ^-- copy_from_template updates the children in the DB
                # but we must also set .children here to avoid overwriting the DB again
            except Exception as exception:  # pylint: disable=broad-except
                TASK_LOGGER.exception('Error importing children for %s', dest_block_key, exc_info=True)
                if self.status.state != UserTaskStatus.FAILED:
                    self.status.fail({'raw_error_msg': str(exception)})
                return
    else:
        # TODO: add filtering by capa_type when V2 library will support different problem types
        try:
            source_blocks = library_api.get_library_blocks(library_key, block_types=None)
            source_block_ids = [str(block.usage_key) for block in source_blocks]
            import_from_blockstore(user_id, store, dest_block, source_block_ids)
            dest_block.source_library_version = str(library.version)
            store.update_item(dest_block, user_id)
        except Exception as exception:  # pylint: disable=broad-except
            TASK_LOGGER.exception('Error importing children for %s', dest_block_key, exc_info=True)
            if self.status.state != UserTaskStatus.FAILED:
                self.status.fail({'raw_error_msg': str(exception)})
            return

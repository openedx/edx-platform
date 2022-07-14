"""
This module contains tasks for asynchronous execution of library xblocks.
"""
import hashlib

from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import PermissionDenied
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import (
    BlockUsageLocator,
    LibraryLocatorV2,
    LibraryUsageLocator,
    LibraryUsageLocatorV2
)
from search.search_engine_base import SearchEngine
from user_tasks.models import UserTaskStatus
from user_tasks.tasks import UserTask
from xblock.fields import Scope

from common.djangoapps.student.auth import has_studio_write_access
from openedx.core.djangoapps.content_libraries import api as library_api
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.djangoapps.xblock.api import load_block
from openedx.core.lib import blockstore_api
from xmodule.capa_module import ProblemBlock
from xmodule.library_content_module import ANY_CAPA_TYPE_VALUE
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

LOGGER = get_task_logger(__name__)


def normalize_key_for_search(library_key):
    """ Normalizes library key for use with search indexing """
    return library_key.replace(version_guid=None, branch=None)


def _import_block(store, user_id, source_block, dest_parent_key):
    """
    Recursively import a blockstore block and its children. See import_from_blockstore above.
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
            user_id=user_id,
            parent_usage_key=dest_parent_key,
            block_type=source_key.block_type,
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
    Filters children by CAPA problem type, if configured
    """
    if usage_key.block_type != "problem":
        return False

    descriptor = store.get_item(usage_key, depth=0)
    assert isinstance(descriptor, ProblemBlock)
    return capa_type in descriptor.problem_types


def _get_library(store, library_key, is_v2_lib):
    """
    Helper method to get either V1 or V2 library.

    Given a library key like "library-v1:ProblemX+PR0B" (V1) or "lib:RG:rg-1" (v2), return the 'library'.

    is_v2_lib (bool) indicates which library storage should be requested:
        True - blockstore (V2 library);
        False - modulestore (V1 library).

    Returns None on error.
    """
    if is_v2_lib:
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
    """ Filters library children by capa type"""
    search_engine = SearchEngine.get_search_engine(index="library_index")
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
    # (This could be slow and use lots of memory, except for the fact that LibrarySourcedBlock which calls this
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
def update_children_task(self, user_id, dest_block_key, version=None):
    """
    Update xBlock's children.

    Re-fetch all matching blocks from the libraries, and copy them as children of dest_block.
    The children will be given new block_ids.

    NOTE: V1 libraies blocks definition ID should be the
    exact same definition ID used in the copy block.

    This method will update dest_block's 'source_library_version' field to
    store the version number of the libraries used, so we easily determine
    if dest_block is up to date or not.
    """
    store = modulestore()
    dest_block_id = BlockUsageLocator.from_string(dest_block_key)
    dest_block = store.get_item(dest_block_id)
    source_blocks = []
    library_key = dest_block.source_library_key
    is_v2_lib = isinstance(library_key, LibraryLocatorV2)

    if version and not is_v2_lib:
        library_key = library_key.replace(branch=ModuleStoreEnum.BranchName.library, version_guid=version)

    library = _get_library(store, library_key, is_v2_lib)
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
                head_validation = not version
                dest_block.children = store.copy_from_template(
                    source_blocks, dest_block.location, user_id, head_validation=head_validation
                )
                dest_block.source_library_version = str(library.location.library_key.version_guid)
                store.update_item(dest_block, user_id)
                # ^-- copy_from_template updates the children in the DB
                # but we must also set .children here to avoid overwriting the DB again
            except Exception as exception:  # pylint: disable=broad-except
                LOGGER.exception('Error importing children for %s', dest_block_key, exc_info=True)
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
            LOGGER.exception('Error importing children for %s', dest_block_key, exc_info=True)
            if self.status.state != UserTaskStatus.FAILED:
                self.status.fail({'raw_error_msg': str(exception)})
            return


def get_import_task_status(dest_block_key):
    """
    Return task status for LibraryUpdateChildrenTask
    """
    args = {'dest_block_key': dest_block_key}
    name = LibraryUpdateChildrenTask.generate_name(args)
    task_status = UserTaskStatus.objects.filter(name=name).order_by('-created').first()
    if task_status:
        return task_status.state

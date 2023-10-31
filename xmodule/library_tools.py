"""
XBlock runtime services for LibraryContentBlock
"""
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import PermissionDenied
from django.conf import settings
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import (
    LibraryLocator,
    LibraryLocatorV2,
    LibraryUsageLocator,
)
from search.search_engine_base import SearchEngine
from typing import Union
from user_tasks.models import UserTaskStatus

from openedx.core.djangoapps.content_libraries import api as library_api
from xmodule.capa_block import ProblemBlock
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import ItemNotFoundError
from openedx.core.djangoapps.content_libraries.tasks import update_children_task
from openedx.core.djangoapps.content_libraries.models import ContentLibrary


def normalize_key_for_search(library_key):
    """ Normalizes library key for use with search indexing """
    return library_key.replace(version_guid=None, branch=None)


class LibraryToolsService:
    """
    Service for LibraryContentBlock.

    Allows to interact with libraries in the modulestore and blockstore.

    Should only be used in the CMS.
    """
    def __init__(self, modulestore, user_id):
        self.store = modulestore
        self.user_id = user_id

    def _get_library(self, library_key):
        """
        Helper method to get either V1 or V2 library.

        Given a library key like "library-v1:ProblemX+PR0B" (V1) or "lib:RG:rg-1" (v2), return the 'library'.

        Returns None on error.
        """

        if isinstance(library_key, LibraryLocatorV2):
            try:
                return library_api.get_library(library_key)
            except ContentLibrary.DoesNotExist:
                return None
        else:
            try:
                return self.store.get_library(
                    library_key, remove_version=False, remove_branch=False, head_validation=False
                )
            except ItemNotFoundError:
                return None

    def get_library_version(self, lib_key):
        """
        Get the version of the given library.

        The return value (library version) could be:
            ObjectID - for V1 library;
            int      - for V2 library.
            None     - if the library does not exist.
        """
        if not isinstance(lib_key, (LibraryLocator, LibraryLocatorV2)):
            try:
                lib_key = LibraryLocator.from_string(lib_key)
                is_v2_lib = False
            except InvalidKeyError:
                lib_key = LibraryLocatorV2.from_string(lib_key)
                is_v2_lib = True
        else:
            is_v2_lib = isinstance(lib_key, LibraryLocatorV2)

        library = self._get_library(lib_key)

        if library:
            if isinstance(lib_key, LibraryLocatorV2):
                return library.version
            # We need to know the library's version so ensure it's set in library.location.library_key.version_guid
            assert library.location.library_key.version_guid is not None
            return library.location.library_key.version_guid
        return None

    def create_block_analytics_summary(self, course_key, block_keys):
        """
        Given a CourseKey and a list of (block_type, block_id) pairs,
        prepare the JSON-ready metadata needed for analytics logging.

        This is [
            {"usage_key": x, "original_usage_key": y, "original_usage_version": z, "descendants": [...]}
        ]
        where the main list contains all top-level blocks, and descendants contains a *flat* list of all
        descendants of the top level blocks, if any.
        """
        def summarize_block(usage_key):
            """ Basic information about the given block """
            orig_key, orig_version = self.store.get_block_original_usage(usage_key)
            return {
                "usage_key": str(usage_key),
                "original_usage_key": str(orig_key) if orig_key else None,
                "original_usage_version": str(orig_version) if orig_version else None,
            }

        result_json = []
        for block_key in block_keys:
            key = course_key.make_usage_key(*block_key)
            info = summarize_block(key)
            info['descendants'] = []
            try:
                block = self.store.get_item(key, depth=None)  # Load the item and all descendants
                children = list(getattr(block, "children", []))
                while children:
                    child_key = children.pop()
                    child = self.store.get_item(child_key)
                    info['descendants'].append(summarize_block(child_key))
                    children.extend(getattr(child, "children", []))
            except ItemNotFoundError:
                pass  # The block has been deleted
            result_json.append(info)
        return result_json

    def _problem_type_filter(self, library, capa_type):
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
            return [key for key in library.children if self._filter_child(key, capa_type)]

    def _filter_child(self, usage_key, capa_type):
        """
        Return the "capa_type" if the block is a problem, otherwise return None.
        """
        if usage_key.block_type != "problem":
            return False

        block = self.store.get_item(usage_key, depth=0)
        assert isinstance(block, ProblemBlock)
        return capa_type in block.problem_types

    def can_use_library_content(self, block):
        """
        Determines whether a modulestore holding a course_id supports libraries.
        """
        return self.store.check_supports(block.location.course_key, 'copy_from_template')

    def trigger_update_children_task(self, dest_block, user_perms=None, version=None):
        """
        Update xBlock's children via an asynchronous task.

        Re-fetch all matching blocks from the libraries, and copy them as children of dest_block.
        The children will be given new block_ids.

        NOTE: V1 libraies blocks definition ID should be the
        exact same definition ID used in the copy block.

        """
        if user_perms and not user_perms.can_write(dest_block.location.course_key):
            raise PermissionDenied()

        if not dest_block.source_library_id:
            dest_block.source_library_version = ""
            return

        source_blocks = []

        library_key = dest_block.source_library_key
        is_v2_lib = isinstance(library_key, LibraryLocatorV2)

        if version and not is_v2_lib:
            library_key = library_key.replace(branch=ModuleStoreEnum.BranchName.library, version_guid=version)

        library = self._get_library(library_key)

        if library is None:
            raise ValueError(f"Requested library {library_key} not found.")
        if user_perms and not user_perms.can_read(library_key):
            raise PermissionDenied()
        update_children_task.delay(self.user_id, str(dest_block.location), version)

    def get_update_children_task_state(self, library_content_block_key) -> Union[str, None]:
        """
        Return task state for most-recently-created update_children task for specified library_content block.

        Options: UserTaskState.{PENDING, IN_PROGRESS, RETRYING, SUCCEEDED, FAILED, CANCELED}
        If no update_childen task exists, returns None.
        """
        args = {'dest_block_key': library_content_block_key}
        name = update_children_task.__class__.generate_name(args)
        return UserTaskStatus.objects.filter(name=name).order_by('-created').first()

    def list_available_libraries(self):
        """
        List all known libraries.

        Collects Only V2 Libaries if the FEATURES[ENABLE_LIBRARY_AUTHORING_MICROFRONTEND] setting is True.
        Otherwise, return all v1 and v2 libraries.
        Returns tuples of (library key, display_name).

        """
        user = User.objects.get(id=self.user_id)
        v1_libs = [
            (lib.location.library_key.replace(version_guid=None, branch=None), lib.display_name)
            for lib in self.store.get_library_summaries()
        ]
        v2_query = library_api.get_libraries_for_user(user)
        v2_libs_with_meta = library_api.get_metadata_from_index(v2_query)
        v2_libs = [(lib.key, lib.title) for lib in v2_libs_with_meta]

        if settings.FEATURES.get('ENABLE_LIBRARY_AUTHORING_MICROFRONTEND'):
            return v2_libs
        return v1_libs + v2_libs

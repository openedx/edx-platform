"""
XBlock runtime services for LibraryContentModule
"""
from django.core.exceptions import PermissionDenied
from opaque_keys.edx.locator import LibraryLocator, LibraryUsageLocator
from search.search_engine_base import SearchEngine
from xmodule.library_content_module import ANY_CAPA_TYPE_VALUE
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.capa_module import CapaDescriptor


def normalize_key_for_search(library_key):
    """ Normalizes library key for use with search indexing """
    return library_key.replace(version_guid=None, branch=None)


class LibraryToolsService(object):
    """
    Service that allows LibraryContentModule to interact with libraries in the
    modulestore.
    """
    def __init__(self, modulestore):
        self.store = modulestore

    def _get_library(self, library_key):
        """
        Given a library key like "library-v1:ProblemX+PR0B", return the
        'library' XBlock with meta-information about the library.

        A specific version may be specified.

        Returns None on error.
        """
        if not isinstance(library_key, LibraryLocator):
            library_key = LibraryLocator.from_string(library_key)

        try:
            return self.store.get_library(
                library_key, remove_version=False, remove_branch=False, head_validation=False
            )
        except ItemNotFoundError:
            return None

    def get_library_version(self, lib_key):
        """
        Get the version (an ObjectID) of the given library.
        Returns None if the library does not exist.
        """
        library = self._get_library(lib_key)
        if library:
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
                "usage_key": unicode(usage_key),
                "original_usage_key": unicode(orig_key) if orig_key else None,
                "original_usage_version": unicode(orig_version) if orig_version else None,
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
                "library": unicode(normalize_key_for_search(library.location.library_key)),
                "content_type": CapaDescriptor.INDEX_CONTENT_TYPE,
                "problem_types": capa_type
            }
            search_result = search_engine.search(field_dictionary=filter_clause)
            results = search_result.get('results', [])
            return [LibraryUsageLocator.from_string(item['data']['id']) for item in results]
        else:
            return [key for key in library.children if self._filter_child(key, capa_type)]

    def _filter_child(self, usage_key, capa_type):
        """
        Filters children by CAPA problem type, if configured
        """
        if usage_key.block_type != "problem":
            return False

        descriptor = self.store.get_item(usage_key, depth=0)
        assert isinstance(descriptor, CapaDescriptor)
        return capa_type in descriptor.problem_types

    def can_use_library_content(self, block):
        """
        Determines whether a modulestore holding a course_id supports libraries.
        """
        return self.store.check_supports(block.location.course_key, 'copy_from_template')

    def update_children(self, dest_block, user_id, user_perms=None, version=None):
        """
        This method is to be used when the library that a LibraryContentModule
        references has been updated. It will re-fetch all matching blocks from
        the libraries, and copy them as children of dest_block. The children
        will be given new block_ids, but the definition ID used should be the
        exact same definition ID used in the library.

        This method will update dest_block's 'source_library_version' field to
        store the version number of the libraries used, so we easily determine
        if dest_block is up to date or not.
        """
        if user_perms and not user_perms.can_write(dest_block.location.course_key):
            raise PermissionDenied()

        if not dest_block.source_library_id:
            dest_block.source_library_version = ""
            return

        source_blocks = []
        library_key = dest_block.source_library_key
        if version:
            library_key = library_key.replace(branch=ModuleStoreEnum.BranchName.library, version_guid=version)
        library = self._get_library(library_key)
        if library is None:
            raise ValueError("Requested library not found.")
        if user_perms and not user_perms.can_read(library_key):
            raise PermissionDenied()
        filter_children = (dest_block.capa_type != ANY_CAPA_TYPE_VALUE)
        if filter_children:
            # Apply simple filtering based on CAPA problem types:
            source_blocks.extend(self._problem_type_filter(library, dest_block.capa_type))
        else:
            source_blocks.extend(library.children)

        with self.store.bulk_operations(dest_block.location.course_key):
            dest_block.source_library_version = unicode(library.location.library_key.version_guid)
            self.store.update_item(dest_block, user_id)
            head_validation = not version
            dest_block.children = self.store.copy_from_template(
                source_blocks, dest_block.location, user_id, head_validation=head_validation
            )
            # ^-- copy_from_template updates the children in the DB
            # but we must also set .children here to avoid overwriting the DB again

    def list_available_libraries(self):
        """
        List all known libraries.
        Returns tuples of (LibraryLocator, display_name)
        """
        return [
            (lib.location.library_key.replace(version_guid=None, branch=None), lib.display_name)
            for lib in self.store.get_libraries()
        ]

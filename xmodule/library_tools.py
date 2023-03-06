"""
XBlock runtime services for LibraryContentBlock
"""
import hashlib

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import PermissionDenied
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryLocator, LibraryUsageLocator, LibraryUsageLocatorV2, BlockUsageLocator
from search.search_engine_base import SearchEngine
from xblock.fields import Scope

from openedx.core.djangoapps.content_libraries import api as library_api
from openedx.core.djangoapps.xblock.api import load_block
from openedx.core.lib import blockstore_api
from common.djangoapps.student.auth import has_studio_write_access
from xmodule.capa_block import ProblemBlock
from xmodule.library_content_block import ANY_CAPA_TYPE_VALUE
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import ItemNotFoundError


def normalize_key_for_search(library_key):
    """ Normalizes library key for use with search indexing """
    return library_key.replace(version_guid=None, branch=None)


class LibraryToolsService:
    """
    Service that allows LibraryContentBlock to interact with libraries in the
    modulestore.
    """
    def __init__(self, modulestore, user_id):
        self.store = modulestore
        self.user_id = user_id

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
        Filters children by CAPA problem type, if configured
        """
        if usage_key.block_type != "problem":
            return False

        descriptor = self.store.get_item(usage_key, depth=0)
        assert isinstance(descriptor, ProblemBlock)
        return capa_type in descriptor.problem_types

    def can_use_library_content(self, block):
        """
        Determines whether a modulestore holding a course_id supports libraries.
        """
        return self.store.check_supports(block.location.course_key, 'copy_from_template')

    def update_children(self, dest_block, user_perms=None, version=None):
        """
        This method is to be used when the library that a LibraryContentBlock
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
            raise ValueError(f"Requested library {library_key} not found.")
        if user_perms and not user_perms.can_read(library_key):
            raise PermissionDenied()
        filter_children = (dest_block.capa_type != ANY_CAPA_TYPE_VALUE)
        if filter_children:
            # Apply simple filtering based on CAPA problem types:
            source_blocks.extend(self._problem_type_filter(library, dest_block.capa_type))
        else:
            source_blocks.extend(library.children)

        with self.store.bulk_operations(dest_block.location.course_key):
            dest_block.source_library_version = str(library.location.library_key.version_guid)
            self.store.update_item(dest_block, self.user_id)
            head_validation = not version
            dest_block.children = self.store.copy_from_template(
                source_blocks, dest_block.location, self.user_id, head_validation=head_validation
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
            for lib in self.store.get_library_summaries()
        ]

    def import_from_blockstore(self, dest_block, blockstore_block_ids):
        """
        Imports a block from a blockstore-based learning context (usually a
        content library) into modulestore, as a new child of dest_block.
        Any existing children of dest_block are replaced.

        This is only used by LibrarySourcedBlock. It should verify first that
        the number of block IDs is reasonable.
        """
        dest_key = dest_block.scope_ids.usage_id
        if not isinstance(dest_key, BlockUsageLocator):
            raise TypeError(f"Destination {dest_key} should be a modulestore course.")
        if self.user_id is None:
            raise ValueError("Cannot check user permissions - LibraryTools user_id is None")

        if len(set(blockstore_block_ids)) != len(blockstore_block_ids):
            # We don't support importing the exact same block twice because it would break the way we generate new IDs
            # for each block and then overwrite existing copies of blocks when re-importing the same blocks.
            raise ValueError("One or more library component IDs is a duplicate.")

        dest_course_key = dest_key.context_key
        user = User.objects.get(id=self.user_id)
        if not has_studio_write_access(user, dest_course_key):
            raise PermissionDenied()

        # Read the source block; this will also confirm that user has permission to read it.
        # (This could be slow and use lots of memory, except for the fact that LibrarySourcedBlock which calls this
        # should be limiting the number of blocks to a reasonable limit. We load them all now instead of one at a
        # time in order to raise any errors before we start actually copying blocks over.)
        orig_blocks = [load_block(UsageKey.from_string(key), user) for key in blockstore_block_ids]

        with self.store.bulk_operations(dest_course_key):
            child_ids_updated = set()

            for block in orig_blocks:
                new_block_id = self._import_block(block, dest_key)
                child_ids_updated.add(new_block_id)

            # Remove any existing children that are no longer used
            for old_child_id in set(dest_block.children) - child_ids_updated:
                self.store.delete_item(old_child_id, self.user_id)
            # If this was called from a handler, it will save dest_block at the end, so we must update
            # dest_block.children to avoid it saving the old value of children and deleting the new ones.
            dest_block.children = self.store.get_item(dest_key).children

    def _import_block(self, source_block, dest_parent_key):
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
            new_block = self.store.get_item(new_block_key)
            if new_block.parent != dest_parent_key:
                raise ValueError(
                    "Expected existing block {} to be a child of {} but instead it's a child of {}".format(
                        new_block_key, dest_parent_key, new_block.parent,
                    )
                )
        except ItemNotFoundError:
            new_block = self.store.create_child(
                user_id=self.user_id,
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
        self.store.update_item(new_block, self.user_id)

        if new_block.has_children:
            # Delete existing children in the new block, which can be reimported again if they still exist in the
            # source library
            for existing_child_key in new_block.children:
                self.store.delete_item(existing_child_key, self.user_id)
            # Now import the children
            for child in source_block.get_children():
                self._import_block(child, new_block_key)

        return new_block_key

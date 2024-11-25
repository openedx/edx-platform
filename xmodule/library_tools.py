"""
<<<<<<< HEAD
XBlock runtime services for LibraryContentBlock
=======
XBlock runtime services for LegacyLibraryContentBlock
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
"""
from __future__ import annotations

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
<<<<<<< HEAD
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from user_tasks.models import UserTaskStatus

from openedx.core.lib import ensure_cms
from openedx.core.djangoapps.content_libraries import api as library_api
from openedx.core.djangoapps.content_libraries import tasks as library_tasks
from xmodule.library_content_block import LibraryContentBlock
from xmodule.library_root_xblock import LibraryRoot as LibraryRootV1
=======
from django.core.exceptions import ObjectDoesNotExist
from opaque_keys.edx.locator import LibraryLocator
from user_tasks.models import UserTaskStatus

from openedx.core.lib import ensure_cms
from openedx.core.djangoapps.content_libraries import tasks as library_tasks
from xmodule.library_content_block import LegacyLibraryContentBlock
from xmodule.modulestore import ModuleStoreEnum
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
from xmodule.modulestore.exceptions import ItemNotFoundError


def normalize_key_for_search(library_key):
    """ Normalizes library key for use with search indexing """
    return library_key.replace(version_guid=None, branch=None)


<<<<<<< HEAD
class LibraryToolsService:
    """
    Service for LibraryContentBlock.

    Allows to interact with libraries in the modulestore and blockstore.
=======
class LegacyLibraryToolsService:
    """
    Service for LegacyLibraryContentBlock.

    Allows to interact with libraries in the modulestore and learning core.
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    Should only be used in the CMS.
    """
    def __init__(self, modulestore, user_id):
        self.store = modulestore
        self.user_id = user_id

<<<<<<< HEAD
    def get_latest_library_version(self, lib_key) -> str | None:
=======
    def get_latest_library_version(self, library_id: str | LibraryLocator) -> str | None:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        """
        Get the version of the given library as string.

        The return value (library version) could be:
            str(<ObjectID>) - for V1 library;
<<<<<<< HEAD
            str(<int>)      - for V2 library.
            None            - if the library does not exist.
        """
        library = library_api.get_v1_or_v2_library(lib_key, version=None)
        if not library:
            return None
        elif isinstance(library, LibraryRootV1):
            # We need to know the library's version so ensure it's set in library.location.library_key.version_guid
            assert library.location.library_key.version_guid is not None
            return str(library.location.library_key.version_guid)
        elif isinstance(library, library_api.ContentLibraryMetadata):
            return str(library.version)

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
=======
            None            - if the library does not exist.
        """
        library_key: LibraryLocator
        if isinstance(library_id, str):
            library_key = LibraryLocator.from_string(library_id)
        else:
            library_key = library_id
        library_key = library_key.for_branch(ModuleStoreEnum.BranchName.library).for_version(None)
        try:
            library = self.store.get_library(
                library_key, remove_version=False, remove_branch=False, head_validation=False
            )
        except ItemNotFoundError:
            return None
        if not library:
            return None
        # We need to know the library's version so ensure it's set in library.location.library_key.version_guid
        assert library.location.library_key.version_guid is not None
        return str(library.location.library_key.version_guid)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    def can_use_library_content(self, block):
        """
        Determines whether a modulestore holding a course_id supports libraries.
        """
        return self.store.check_supports(block.location.course_key, 'copy_from_template')

<<<<<<< HEAD
    def trigger_library_sync(self, dest_block: LibraryContentBlock, library_version: str | int | None) -> None:
=======
    def trigger_library_sync(self, dest_block: LegacyLibraryContentBlock, library_version: str | None) -> None:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        """
        Queue task to synchronize the children of `dest_block` with it source library (at `library_version` or latest).

        Raises ObjectDoesNotExist if library/version cannot be found.

        The task will:
        * Load that library at `dest_block.source_library_id` and `library_version`.
          * If `library_version` is None, load the latest.
          * Update `dest_block.source_library_version` based on what is loaded.
        * Ensure that `dest_block` has children corresponding to all matching source library blocks.
          * Considered fields of `dest_block` include: `source_library_id`, `source_library_version`, `capa_type`.
            library version, and upate `dest_block.source_library_version` to match.
        * Derive each child block id as a function of `dest_block`'s id and the library block's definition id.
        * Follow these important create/update/delete semantics for children:
          * When a matching library child DOES NOT EXIT in `dest_block.children`: import it in as a new block.
          * When a matching library child ALREADY EXISTS in `dest_block.children`: re-import its definition, clobbering
            any content updates in this existing child, but preserving any settings overrides in the existing child.
          * When a block in `dest_block.children` DOES NOT MATCH any library children: delete it from
            `dest_block.children`.
        """
        ensure_cms("library_content block children may only be synced in a CMS context")
<<<<<<< HEAD
        if not isinstance(dest_block, LibraryContentBlock):
=======
        if not isinstance(dest_block, LegacyLibraryContentBlock):
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            raise ValueError(f"Can only sync children for library_content blocks, not {dest_block.tag} blocks.")
        if not dest_block.source_library_id:
            dest_block.source_library_version = ""
            return
<<<<<<< HEAD
        library_key = dest_block.source_library_key
        if not library_api.get_v1_or_v2_library(library_key, version=library_version):
            if library_version:
                raise ObjectDoesNotExist(f"Version {library_version} of library {library_key} not found.")
            raise ObjectDoesNotExist(f"Library {library_key} not found.")
=======
        library_key = dest_block.source_library_key.for_branch(
            ModuleStoreEnum.BranchName.library
        ).for_version(library_version)
        try:
            self.store.get_library(library_key, remove_version=False, remove_branch=False, head_validation=False)
        except ItemNotFoundError as exc:
            if library_version:
                raise ObjectDoesNotExist(f"Version {library_version} of library {library_key} not found.") from exc
            raise ObjectDoesNotExist(f"Library {library_key} not found.") from exc
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

        # TODO: This task is synchronous until we can figure out race conditions with import.
        # These race conditions lead to failed imports of library content from course import.
        # See: TNL-11339, https://github.com/openedx/edx-platform/issues/34029 for more info.
        library_tasks.sync_from_library.apply(
            kwargs=dict(
                user_id=self.user_id,
                dest_block_id=str(dest_block.scope_ids.usage_id),
                library_version=library_version,
            ),
        )

<<<<<<< HEAD
    def trigger_duplication(self, source_block: LibraryContentBlock, dest_block: LibraryContentBlock) -> None:
=======
    def trigger_duplication(
        self, source_block: LegacyLibraryContentBlock, dest_block: LegacyLibraryContentBlock
    ) -> None:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        """
        Queue a task to duplicate the children of `source_block` to `dest_block`.
        """
        ensure_cms("library_content block children may only be duplicated in a CMS context")
<<<<<<< HEAD
        if not isinstance(dest_block, LibraryContentBlock):
=======
        if not isinstance(dest_block, LegacyLibraryContentBlock):
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            raise ValueError(f"Can only duplicate children for library_content blocks, not {dest_block.tag} blocks.")
        if source_block.scope_ids.usage_id.context_key != source_block.scope_ids.usage_id.context_key:
            raise ValueError(
                "Cannot duplicate_children across different learning contexts "
                f"(source={source_block.scope_ids.usage_id}, dest={dest_block.scope_ids.usage_id})"
            )
        if source_block.source_library_key != dest_block.source_library_key:
            raise ValueError(
                "Cannot duplicate_children across different source libraries or versions thereof "
                f"({source_block.source_library_key=}, {dest_block.source_library_key=})."
            )
        library_tasks.duplicate_children.delay(
            user_id=self.user_id,
            source_block_id=str(source_block.scope_ids.usage_id),
            dest_block_id=str(dest_block.scope_ids.usage_id),
        )

<<<<<<< HEAD
    def are_children_syncing(self, library_content_block: LibraryContentBlock) -> bool:
=======
    def are_children_syncing(self, library_content_block: LegacyLibraryContentBlock) -> bool:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        """
        Is a task currently running to sync the children of `library_content_block`?

        Only checks the latest task (so that this block's state can't get permanently messed up by
        some older task that's stuck in PENDING).
        """
        args = {'dest_block_id': library_content_block.scope_ids.usage_id}
        name = library_tasks.LibrarySyncChildrenTask.generate_name(args)
        status = UserTaskStatus.objects.filter(name=name).order_by('-created').first()
        return status and status.state in [
            UserTaskStatus.IN_PROGRESS, UserTaskStatus.PENDING, UserTaskStatus.RETRYING
        ]

    def list_available_libraries(self):
        """
<<<<<<< HEAD
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
        v2_libs_with_meta = library_api.get_metadata(v2_query)
        v2_libs = [(lib.key, lib.title) for lib in v2_libs_with_meta]

        if settings.FEATURES.get('ENABLE_LIBRARY_AUTHORING_MICROFRONTEND'):
            return v2_libs
        return v1_libs + v2_libs
=======
        List all known legacy libraries.

        Returns tuples of (library key, display_name).
        """
        user = User.objects.get(id=self.user_id)
        return [
            (lib.location.library_key.replace(version_guid=None, branch=None), lib.display_name)
            for lib in self.store.get_library_summaries()
        ]
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

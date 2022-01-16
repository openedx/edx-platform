"""
Helper code for working with Blockstore bundles that contain OLX
"""

import logging  # lint-amnesty, pylint: disable=wrong-import-order

from functools import lru_cache  # lint-amnesty, pylint: disable=wrong-import-order
from opaque_keys.edx.locator import BundleDefinitionLocator, LibraryUsageLocatorV2
from xblock.core import XBlock
from xblock.plugin import PluginMissingError

from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.djangoapps.xblock.runtime.blockstore_runtime import xml_for_definition
from openedx.core.djangoapps.xblock.runtime.olx_parsing import (
    BundleFormatException,
    definition_for_include,
    parse_xblock_include,
)
from openedx.core.djangolib.blockstore_cache import (
    BundleCache,
    get_bundle_direct_links_with_cache,
    get_bundle_files_cached,
    get_bundle_file_metadata_with_cache,
    get_bundle_version_number,
)
from openedx.core.lib import blockstore_api

log = logging.getLogger(__name__)


@lru_cache()
def bundle_uuid_for_library_key(library_key):
    """
    Given a library slug, look up its bundle UUID.
    Can be cached aggressively since bundle UUID is immutable.

    May raise ContentLibrary.DoesNotExist
    """
    library_metadata = ContentLibrary.objects.get_by_key(library_key)
    return library_metadata.bundle_uuid


def usage_for_child_include(parent_usage, parent_definition, parsed_include):
    """
    Get the usage ID for a child XBlock, given the parent's keys and the
    <xblock-include /> element that specifies the child.

    Consider two bundles, one with three definitions:
        main-unit, html1, subunit1
    And a second bundle with two definitions:
        unit1, html1
    Note that both bundles have a definition called "html1". Now, with the
    following tree structure, where "unit/unit1" and the second "html/html1"
    are in a linked bundle:

    <unit> in unit/main-unit/definition.xml
        <xblock-include definition="html/html1" />
        <xblock-include definition="unit/subunit1" />
            <xblock-include source="linked_bundle" definition="unit/unit1" usage="alias1" />
                <xblock-include definition="html/html1" />

    The following usage IDs would result:

    main-unit
        html1
        subunit1
            alias1
                alias1-html1

    Notice that "html1" in the linked bundle is prefixed so its ID stays
    unique from the "html1" in the original library.
    """
    assert isinstance(parent_usage, LibraryUsageLocatorV2)
    usage_id = parsed_include.usage_hint if parsed_include.usage_hint else parsed_include.definition_id
    library_bundle_uuid = bundle_uuid_for_library_key(parent_usage.context_key)
    # Is the parent usage from the same bundle as the library?
    parent_usage_from_library_bundle = parent_definition.bundle_uuid == library_bundle_uuid
    if not parent_usage_from_library_bundle:
        # This XBlock has been linked in to the library via a chain of one
        # or more bundle links. In order to keep usage_id collisions from
        # happening, any descdenants of the first linked block must have
        # their usage_id prefixed with the parent usage's usage_id.
        # (It would be possible to only change the prefix when the block is
        # a child of a block with an explicit usage="" attribute on its
        # <xblock-include> but that requires much more complex logic.)
        usage_id = parent_usage.usage_id + "-" + usage_id
    return LibraryUsageLocatorV2(
        lib_key=parent_usage.lib_key,
        block_type=parsed_include.block_type,
        usage_id=usage_id,
    )


class LibraryBundle:
    """
    Wrapper around a Content Library Blockstore bundle that contains OLX.
    """

    def __init__(self, library_key, bundle_uuid, draft_name=None):
        """
        Instantiate this wrapper for the bundle with the specified library_key,
        UUID, and optionally the specified draft name.
        """
        self.library_key = library_key
        self.bundle_uuid = bundle_uuid
        self.draft_name = draft_name
        self.cache = BundleCache(bundle_uuid, draft_name)

    def get_olx_files(self):
        """
        Get the list of OLX files in this bundle (using a heuristic)

        Because this uses a heuristic, it will only return files with filenames
        that seem like OLX files that are in the expected locations of OLX
        files. They are not guaranteed to be valid OLX nor will OLX files in
        nonstandard locations be returned.

        Example return value: [
            'html/intro/definition.xml',
            'unit/unit1/definition.xml',
        ]
        """
        bundle_files = get_bundle_files_cached(self.bundle_uuid, draft_name=self.draft_name)
        return [f.path for f in bundle_files if f.path.endswith("/definition.xml")]

    def definition_for_usage(self, usage_key):
        """
        Given the usage key for an XBlock in this library bundle, return the
        BundleDefinitionLocator which specifies the actual XBlock definition (as
        a path to an OLX in a specific blockstore bundle).

        Must return a BundleDefinitionLocator if the XBlock exists in this
        context, or None otherwise.

        For a content library, the rules are simple:
        * If the usage key points to a block in this library, the filename
          (definition) of the OLX file is always
            {block_type}/{usage_id}/definition.xml
          Each library has exactly one usage per definition for its own blocks.
        * However, block definitions from other content libraries may be linked
          into this library via <xblock-include ... /> directives. In that case,
          it's necessary to inspect every OLX file in this library that might
          have an <xblock-include /> directive in order to find what external
          block the usage ID refers to.
        """
        # Now that we know the library/bundle, find the block's definition
        if self.draft_name:
            version_arg = {"draft_name": self.draft_name}
        else:
            version_arg = {"bundle_version": get_bundle_version_number(self.bundle_uuid)}
        olx_path = f"{usage_key.block_type}/{usage_key.usage_id}/definition.xml"
        try:
            get_bundle_file_metadata_with_cache(self.bundle_uuid, olx_path, **version_arg)
            return BundleDefinitionLocator(self.bundle_uuid, usage_key.block_type, olx_path, **version_arg)
        except blockstore_api.BundleFileNotFound:
            # This must be a usage of a block from a linked bundle. One of the
            # OLX files in this bundle contains an <xblock-include usage="..."/>
            bundle_includes = self.get_bundle_includes()
            try:
                return bundle_includes[usage_key]
            except KeyError:
                return None

    def get_all_usages(self):
        """
        Get usage keys of all the blocks in this bundle
        """
        usage_keys = []
        for olx_file_path in self.get_olx_files():
            block_type, usage_id, _unused = olx_file_path.split('/')
            usage_key = LibraryUsageLocatorV2(self.library_key, block_type, usage_id)
            usage_keys.append(usage_key)

        return usage_keys

    def get_top_level_usages(self):
        """
        Get the set of usage keys in this bundle that have no parent.
        """
        own_usage_keys = self.get_all_usages()
        usage_keys_with_parents = self.get_bundle_includes().keys()
        return [usage_key for usage_key in own_usage_keys if usage_key not in usage_keys_with_parents]

    def get_bundle_includes(self):
        """
        Scan through the bundle and all linked bundles as needed to generate
        a complete list of all the blocks that are included as
        child/grandchild/... blocks of the blocks in this bundle.

        Returns a dict of {usage_key -> BundleDefinitionLocator}

        Blocks in the bundle that have no parent are not included.
        """
        cache_key = ("bundle_includes", )
        usages_found = self.cache.get(cache_key)
        if usages_found is not None:
            return usages_found

        usages_found = {}

        def add_definitions_children(usage_key, def_key):
            """
            Recursively add any children of the given XBlock usage+definition to
            usages_found.
            """
            if not does_block_type_support_children(def_key.block_type):
                return
            try:
                xml_node = xml_for_definition(def_key)
            except:  # pylint:disable=bare-except
                log.exception(f"Unable to load definition {def_key}")
                return

            for child in xml_node:
                if child.tag != 'xblock-include':
                    continue
                try:
                    parsed_include = parse_xblock_include(child)
                    child_usage = usage_for_child_include(usage_key, def_key, parsed_include)
                    child_def_key = definition_for_include(parsed_include, def_key)
                except BundleFormatException:
                    log.exception(f"Unable to parse a child of {def_key}")
                    continue
                usages_found[child_usage] = child_def_key
                add_definitions_children(child_usage, child_def_key)

        # Find all the definitions in this bundle and recursively add all their descendants:
        bundle_files = get_bundle_files_cached(self.bundle_uuid, draft_name=self.draft_name)
        if self.draft_name:
            version_arg = {"draft_name": self.draft_name}
        else:
            version_arg = {"bundle_version": get_bundle_version_number(self.bundle_uuid)}
        for bfile in bundle_files:
            if not bfile.path.endswith("/definition.xml") or bfile.path.count('/') != 2:
                continue  # Not an OLX file.
            block_type, usage_id, _unused = bfile.path.split('/')
            def_key = BundleDefinitionLocator(
                bundle_uuid=self.bundle_uuid,
                block_type=block_type,
                olx_path=bfile.path,
                **version_arg
            )
            usage_key = LibraryUsageLocatorV2(self.library_key, block_type, usage_id)
            add_definitions_children(usage_key, def_key)

        self.cache.set(cache_key, usages_found)
        return usages_found

    def does_definition_have_unpublished_changes(self, definition_key):
        """
        Given the defnition key of an XBlock, which exists in an OLX file like
            problem/quiz1/definition.xml
        Check if the bundle's draft has _any_ unpublished changes in the
            problem/quiz1/
        directory.
        """
        if self.draft_name is None:
            return False  # No active draft so can't be changes
        prefix = self.olx_prefix(definition_key)
        return prefix in self._get_changed_definitions()

    def _get_changed_definitions(self):
        """
        Helper method to get a list of all paths with changes, where a path is
            problem/quiz1/
        Or similar (a type and an ID), excluding 'definition.xml'
        """
        cached_result = self.cache.get(('changed_definition_prefixes', ))
        if cached_result is not None:
            return cached_result
        changed = []
        bundle_files = get_bundle_files_cached(self.bundle_uuid, draft_name=self.draft_name)
        for file_ in bundle_files:
            if getattr(file_, 'modified', False) and file_.path.count('/') >= 2:
                (type_part, id_part, _rest) = file_.path.split('/', 2)
                prefix = type_part + '/' + id_part + '/'
                if prefix not in changed:
                    changed.append(prefix)
        self.cache.set(('changed_definition_prefixes', ), changed)
        return changed

    def has_changes(self):
        """
        Helper method to check if this OLX bundle has any pending changes,
        including any deleted blocks.

        Returns a tuple of (
            has_unpublished_changes,
            has_unpublished_deletes,
        )
        Where has_unpublished_changes is true if there is any type of change,
        including deletes, and has_unpublished_deletes is only true if one or
        more blocks has been deleted since the last publish.
        """
        if not self.draft_name:
            return (False, False)
        cached_result = self.cache.get(('has_changes', ))
        if cached_result is not None:
            return cached_result
        draft_files = get_bundle_files_cached(self.bundle_uuid, draft_name=self.draft_name)

        has_unpublished_changes = False
        has_unpublished_deletes = False

        for file_ in draft_files:
            if getattr(file_, 'modified', False):
                has_unpublished_changes = True
                break

        if not has_unpublished_changes:
            # Check if any links have changed:
            old_links = set(get_bundle_direct_links_with_cache(self.bundle_uuid).items())
            new_links = set(get_bundle_direct_links_with_cache(self.bundle_uuid, draft_name=self.draft_name).items())
            has_unpublished_changes = new_links != old_links

        published_file_paths = {f.path for f in get_bundle_files_cached(self.bundle_uuid)}
        draft_file_paths = {f.path for f in draft_files}
        for file_path in published_file_paths:
            if file_path not in draft_file_paths:
                has_unpublished_changes = True
                if file_path.endswith('/definition.xml'):
                    # only set 'has_unpublished_deletes' if the actual main definition XML
                    # file was deleted, not if only some asset file was deleted, etc.
                    has_unpublished_deletes = True
                    break

        result = (has_unpublished_changes, has_unpublished_deletes)
        self.cache.set(('has_changes', ), result)
        return result

    def get_static_prefix_for_definition(self, definition_key):
        """
        Given a definition key, get the path prefix used for all (public) static
        asset files.

        Example: problem/quiz1/static/
        """
        return self.olx_prefix(definition_key) + 'static/'

    def get_static_files_for_definition(self, definition_key):
        """
        Return a list of the static asset files related with a particular XBlock
        definition.

        If the bundle contains files like:
            problem/quiz1/definition.xml
            problem/quiz1/static/image1.png
        Then this will return
            [BundleFileData(path="image1.png", size, url, hash_digest)]
        """
        path_prefix = self.get_static_prefix_for_definition(definition_key)
        path_prefix_len = len(path_prefix)
        return [
            blockstore_api.BundleFileData(
                path=f.path[path_prefix_len:],
                size=f.size,
                url=f.url,
                hash_digest=f.hash_digest,
            )
            for f in get_bundle_files_cached(self.bundle_uuid, draft_name=self.draft_name)
            if f.path.startswith(path_prefix)
        ]

    def get_last_published_time(self):
        """
        Return the timestamp when the current library was last published. If the
        current draft has never been published, return 0.
        """
        cache_key = ("last_published_time", )
        usages_found = self.cache.get(cache_key)
        if usages_found is not None:
            return usages_found
        version = get_bundle_version_number(self.bundle_uuid)
        if version == 0:
            return None
        last_published_time = blockstore_api.get_bundle_version(self.bundle_uuid, version).created_at
        self.cache.set(cache_key, last_published_time)
        return last_published_time

    @staticmethod
    def olx_prefix(definition_key):
        """
        Given a definition key in a compatible bundle, whose olx_path refers to
            block_type/some_id/definition.xml
        Return the "folder name" / "path prefix"
            block-type/some_id/

        This method is here rather than a method of BundleDefinitionLocator
        because BundleDefinitionLocator is more generic and doesn't require
        that its olx_path always ends in /definition.xml
        """
        if not definition_key.olx_path.endswith('/definition.xml'):
            raise ValueError
        return definition_key.olx_path[:-14]  # Remove 'definition.xml', keep trailing slash


def does_block_type_support_children(block_type):
    """
    Does the specified block type (e.g. "html", "vertical") support child
    blocks?
    """
    try:
        return XBlock.load_class(block_type).has_children
    except PluginMissingError:
        # We don't know if this now-uninstalled block type had children
        # but to be conservative, assume it may have.
        return True

"""
A runtime designed to work with Blockstore, reading and writing
XBlock field data directly from Blockstore.
"""

import logging
import os.path

from lxml import etree
from opaque_keys.edx.locator import BundleDefinitionLocator
from xblock.exceptions import NoSuchDefinition, NoSuchUsage
from xblock.fields import ScopeIds

from openedx.core.djangoapps.xblock.learning_context.manager import get_learning_context_impl
from openedx.core.djangoapps.xblock.runtime.runtime import XBlockRuntime
from openedx.core.djangoapps.xblock.runtime.olx_parsing import parse_xblock_include, BundleFormatException
from openedx.core.djangoapps.xblock.runtime.serializer import serialize_xblock
from openedx.core.djangolib.blockstore_cache import (
    BundleCache,
    get_bundle_file_data_with_cache,
    get_bundle_file_metadata_with_cache,
)
from openedx.core.lib import blockstore_api

log = logging.getLogger(__name__)


class BlockstoreXBlockRuntime(XBlockRuntime):
    """
    A runtime designed to work with Blockstore, reading and writing
    XBlock field data directly from Blockstore.
    """
    def parse_xml_file(self, fileobj, id_generator=None):
        raise NotImplementedError("Use parse_olx_file() instead")

    def get_block(self, usage_id, for_parent=None):
        """
        Create an XBlock instance in this runtime.

        Args:
            usage_key(OpaqueKey): identifier used to find the XBlock class and data.
        """
        def_id = self.id_reader.get_definition_id(usage_id)
        if def_id is None:
            raise ValueError(f"Definition not found for usage {usage_id}")
        if not isinstance(def_id, BundleDefinitionLocator):
            raise TypeError("This runtime can only load blocks stored in Blockstore bundles.")
        try:
            block_type = self.id_reader.get_block_type(def_id)
        except NoSuchDefinition:
            raise NoSuchUsage(repr(usage_id))  # lint-amnesty, pylint: disable=raise-missing-from
        keys = ScopeIds(self.user_id, block_type, def_id, usage_id)

        if self.system.authored_data_store.has_cached_definition(def_id):
            return self.construct_xblock(block_type, keys, for_parent=for_parent)
        else:
            # We need to load this block's field data from its OLX file in blockstore:
            xml_node = xml_for_definition(def_id)
            if xml_node.get("url_name", None):
                log.warning("XBlock at %s should not specify an old-style url_name attribute.", def_id.olx_path)
            block_class = self.mixologist.mix(self.load_block_type(block_type))
            if hasattr(block_class, 'parse_xml_new_runtime'):
                # This is a (former) XModule with messy XML parsing code; let its parse_xml() method continue to work
                # as it currently does in the old runtime, but let this parse_xml_new_runtime() method parse the XML in
                # a simpler way that's free of tech debt, if defined.
                # In particular, XmlMixin doesn't play well with this new runtime, so this is mostly about
                # bypassing that mixin's code.
                # When a former XModule no longer needs to support the old runtime, its parse_xml_new_runtime method
                # should be removed and its parse_xml() method should be simplified to just call the super().parse_xml()
                # plus some minor additional lines of code as needed.
                block = block_class.parse_xml_new_runtime(xml_node, runtime=self, keys=keys)
            else:
                block = block_class.parse_xml(xml_node, runtime=self, keys=keys, id_generator=None)
            # Update field data with parsed values. We can't call .save() because it will call save_block(), below.
            block.force_save_fields(block._get_fields_to_save())  # pylint: disable=protected-access
            self.system.authored_data_store.cache_fields(block)
            # There is no way to set the parent via parse_xml, so do what
            # HierarchyMixin would do:
            if for_parent is not None:
                block._parent_block = for_parent  # pylint: disable=protected-access
                block._parent_block_id = for_parent.scope_ids.usage_id  # pylint: disable=protected-access
            return block

    def add_node_as_child(self, block, node, id_generator=None):
        """
        This runtime API should normally be used via
        runtime.get_block() -> block.parse_xml() -> runtime.add_node_as_child
        """
        try:
            parsed_include = parse_xblock_include(node)
        except BundleFormatException:
            # We need to log the XBlock ID or this will be hard to debug
            log.error("BundleFormatException when parsing XBlock %s", block.scope_ids.usage_id)
            raise  # Also log details and stack trace
        self.add_child_include(block, parsed_include)

    def add_child_include(self, block, parsed_include):
        """
        Given an XBlockInclude tuple that represents a new <xblock-include />
        node, add it as a child of the specified XBlock. This is the only
        supported API for adding a new child to an XBlock - one cannot just
        modify block.children to append a usage ID, since that doesn't provide
        enough information to serialize the block's <xblock-include /> elements.
        """
        self.system.children_data_store.append_include(block, parsed_include)
        block.children = self.system.children_data_store.get(block, 'children')

    def child_includes_of(self, block):
        """
        Get the list of <xblock-include /> directives that define the children
        of this block's definition.
        """
        return self.system.children_data_store.get_includes(block)

    def save_block(self, block):
        """
        Save any pending field data values to Blockstore.

        This gets called by block.save() - do not call this directly.
        """
        if not self.system.authored_data_store.has_changes(block):
            return  # No changes, so no action needed.
        definition_key = block.scope_ids.def_id
        if definition_key.draft_name is None:
            raise RuntimeError(
                "The Blockstore runtime does not support saving changes to blockstore without a draft. "
                "Are you making changes to UserScope.NONE fields from the LMS rather than Studio?"
            )
        # Verify that the user has permission to write to authored data in this
        # learning context:
        if self.user is not None:
            learning_context = get_learning_context_impl(block.scope_ids.usage_id)
            if not learning_context.can_edit_block(self.user, block.scope_ids.usage_id):
                log.warning("User %s does not have permission to edit %s", self.user.username, block.scope_ids.usage_id)
                raise RuntimeError("You do not have permission to edit this XBlock")
        olx_str, static_files = serialize_xblock(block)
        # Write the OLX file to the bundle:
        draft_uuid = blockstore_api.get_or_create_bundle_draft(
            definition_key.bundle_uuid, definition_key.draft_name
        ).uuid
        olx_path = definition_key.olx_path
        blockstore_api.write_draft_file(draft_uuid, olx_path, olx_str)
        # And the other files, if any:
        olx_static_path = os.path.dirname(olx_path) + '/static/'
        for fh in static_files:
            new_path = olx_static_path + fh.name
            blockstore_api.write_draft_file(draft_uuid, new_path, fh.data)
        # Now invalidate the blockstore data cache for the bundle:
        BundleCache(definition_key.bundle_uuid, draft_name=definition_key.draft_name).clear()

    def _lookup_asset_url(self, block, asset_path):
        """
        Return an absolute URL for the specified static asset file that may
        belong to this XBlock.

        e.g. if the XBlock settings have a field value like "/static/foo.png"
        then this method will be called with asset_path="foo.png" and should
        return a URL like https://cdn.none/xblock/f843u89789/static/foo.png

        If the asset file is not recognized, return None
        """
        if '..' in asset_path:
            return None  # Illegal path
        definition_key = block.scope_ids.def_id
        # Compute the full path to the static file in the bundle,
        # e.g. "problem/prob1/static/illustration.svg"
        expanded_path = os.path.dirname(definition_key.olx_path) + '/static/' + asset_path
        try:
            metadata = get_bundle_file_metadata_with_cache(
                bundle_uuid=definition_key.bundle_uuid,
                path=expanded_path,
                bundle_version=definition_key.bundle_version,
                draft_name=definition_key.draft_name,
            )
        except blockstore_api.BundleFileNotFound:
            log.warning("XBlock static file not found: %s for %s", asset_path, block.scope_ids.usage_id)
            return None
        # Make sure the URL is one that will work from the user's browser,
        # not one that only works from within a docker container:
        url = blockstore_api.force_browser_url(metadata.url)
        return url


def xml_for_definition(definition_key):
    """
    Method for loading OLX from Blockstore and parsing it to an etree.
    """
    try:
        xml_str = get_bundle_file_data_with_cache(
            bundle_uuid=definition_key.bundle_uuid,
            path=definition_key.olx_path,
            bundle_version=definition_key.bundle_version,
            draft_name=definition_key.draft_name,
        )
    except blockstore_api.BundleFileNotFound:
        raise NoSuchDefinition("OLX file {} not found in bundle {}.".format(  # lint-amnesty, pylint: disable=raise-missing-from
            definition_key.olx_path, definition_key.bundle_uuid,
        ))
    node = etree.fromstring(xml_str)
    return node

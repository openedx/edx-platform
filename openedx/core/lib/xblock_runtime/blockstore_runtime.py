"""
A runtime designed to work with Blockstore, reading and writing
XBlock field data directly from Blockstore.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from lxml import etree
import requests
from xblock.exceptions import XBlockNotFoundError
from xblock.fields import ScopeIds

from openedx.core.lib.blockstore_api import which_olx_file_contains
from openedx.core.lib.xblock_runtime.blockstore_kvs import collect_parsed_fields
from openedx.core.lib.xblock_keys import global_context, BundleDefinitionLocator

from .runtime import XBlockRuntime


class BlockstoreXBlockRuntime(XBlockRuntime):
    """
    A runtime designed to work with Blockstore, reading and writing
    XBlock field data directly from Blockstore.
    """
    def __init__(self, *args, **kwargs):
        super(BlockstoreXBlockRuntime, self).__init__(*args, **kwargs)
        self._parsed_olx_files = set()

    def parse_xml_file(self, fileobj, id_generator=None):
        raise NotImplementedError("Use parse_olx_file() instead")

    @staticmethod
    def _definition_key_from_node(bundle_uuid, node):
        """
        Helper code used by _parse_and_cache_olx and add_node_as_child
        """
        block_type = node.tag
        # remove xblock-family attribute
        node.attrib.pop('xblock-family', None)
        # Get the definition ID:
        definition_id = node.attrib.pop('url_name', None)
        if not definition_id:
            raise KeyError("Root block is missing a url_name attribute.")

        return BundleDefinitionLocator(
            bundle_uuid=bundle_uuid,
            block_type=block_type,
            definition_id=definition_id,
        )

    def _parse_and_cache_olx(self, bundle_uuid, data_url):
        """
        Load the authored field data for all XBlocks in the given
        OLX file.
        """
        key = (bundle_uuid, data_url)
        if key in self._parsed_olx_files:
            return
        with requests.get(data_url, stream=True) as r:
            xml_raw = r.content

        node = etree.fromstring(xml_raw)
        definition_key = self._definition_key_from_node(bundle_uuid, node)
        block_type = definition_key.block_type
        # At this point, we don't know what context/usage this OLX is loaded for.
        # For now, while we are simply caching the authored OLX data, so set the
        # usage_id (and learning context) to the global context. Later, specific
        # usages of this block's definition can be instantiated via get_block()
        # TODO: confirm that no XBlocks read/use the usage_id during this step.
        usage_id = global_context.make_usage_key(definition_key)
        scope_ids = ScopeIds(self.user_id, block_type, definition_key, usage_id)

        block_class = self.mixologist.mix(self.load_block_type(block_type))

        with collect_parsed_fields():
            block = block_class.parse_xml(node, self, scope_ids, None)
            block.save()  # Cache field data in the KVS

        self._parsed_olx_files.add(key)

    def get_block(self, usage_id, for_parent=None):
        """
        Create an XBlock instance in this runtime.
        """
        def_id = self.id_reader.get_definition_id(usage_id)
        if not isinstance(def_id, BundleDefinitionLocator):
            raise TypeError("This runtime can only load blocks stored in Blockstore bundles.")

        olx_file = which_olx_file_contains(def_id)
        if olx_file is None:
            raise XBlockNotFoundError("Could not find definition {}".format(def_id))

        # TODO: permissions checks

        self._parse_and_cache_olx(def_id.bundle_uuid, olx_file.data_url)

        return super(BlockstoreXBlockRuntime, self).get_block(usage_id, for_parent=for_parent)

    def add_node_as_child(self, block, node, id_generator=None):
        """
        This runtime API should normally be used via
        get_block() -> _parse_and_cache_olx -> parse_xml
        """
        bundle_uuid = block.scope_ids.def_id.bundle_uuid
        definition_key = self._definition_key_from_node(bundle_uuid, node)
        block_type = definition_key.block_type
        context_key = block.scope_ids.usage_id.context_key
        # We can't generate a proper usage_id for this block at this point, since
        # we'd need a usage-specific block_id/usage_id, and we don't have one.
        # But normally this method is only used when parsing XML to extract
        # authored data, so the usage key doesn't actually get used at this point.
        usage_id = context_key.make_usage_key(definition_key, usage_id=None)
        scope_ids = ScopeIds(self.user_id, block_type, definition_key, usage_id)

        block_class = self.mixologist.mix(self.load_block_type(block_type))
        child_block = block_class.parse_xml(node, self, scope_ids, None)
        block.children.append(usage_id)
        # And save the updated fields to the key value store:
        child_block.save()
        block.save()

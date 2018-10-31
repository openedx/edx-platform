from __future__ import absolute_import, division, print_function, unicode_literals
from lxml import etree

from xblock.exceptions import XBlockNotFoundError
from xblock.fields import ScopeIds

from openedx.core.lib.blockstore_api import get_bundle_file_data
from openedx.core.lib.xblock_runtime.blockstore_kvs import collect_parsed_fields
from openedx.core.lib.xblock_keys import LearningContextKey, BundleDefinitionLocator

from .runtime import XBlockRuntime


class BlockstoreXBlockRuntime(XBlockRuntime):
    """
    A runtime designed to work with Blockstore, reading and writing
    XBlock field data directly from Blockstore.
    """

    def parse_xml_file(self, fileobj, id_generator=None):
        raise NotImplementedError("Use parse_olx_file() instead")

    def parse_olx_file(self, bundle_uuid, olx_path, context_key):
        """
        Parse the root XBlock defined in the given bundle, load it and its children's
        fields to memory (until the current blockstore_transaction() ends),
        and return the usage key of the root block.

        Once this method has been used, get the actual block using
        runtime.get_block(usage_key)

        Raises:
            XBlockNotFoundError if the olx path is invalid
        """
        assert isinstance(context_key, LearningContextKey)
        xml_raw = get_bundle_file_data(bundle_uuid, olx_path)
        if xml_raw is None:
            raise XBlockNotFoundError("OLX file not found")

        node = etree.fromstring(xml_raw)
        block_type = node.tag
        # remove xblock-family attribute
        node.attrib.pop('xblock-family', None)
        # Get the definition ID:
        definition_id = node.attrib.pop('url_name', None)
        if not definition_id:
            warnings.warn(
                "XBlock OLX root node in {} has no url_name: using filename instead. "
                "All XBlock nodes in an OLX file should have a unique url_name.".format(olx_path),
                stacklevel=2,
            )
            definition_id = olx_path.rpartition('/')[2].rpartition('.')[0]

        definition_key = BundleDefinitionLocator(
            bundle_uuid=bundle_uuid,
            olx_path=olx_path,
            block_type=block_type,
            definition_id=definition_id
        )
        usage_key = context_key.make_usage_key(definition_key)
        scope_ids = ScopeIds(self.user_id, block_type, definition_key, usage_key)

        block_class = self.mixologist.mix(self.load_block_type(block_type))

        with collect_parsed_fields():
            block = block_class.parse_xml(node, self, scope_ids, None)

        return usage_key

    def add_node_as_child(self, block, node, id_generator=None):
        raise NotImplementedError("Todo: support child blocks")

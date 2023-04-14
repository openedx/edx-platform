"""
Code for serializing a modulestore XBlock to OLX suitable for import into
Blockstore.
"""
import logging
import os
from collections import namedtuple

from lxml import etree

from openedx.core.djangoapps.olx_rest_api import adapters

log = logging.getLogger(__name__)

# A static file required by an XBlock
StaticFile = namedtuple('StaticFile', ['name', 'url', 'data'])


class XBlockSerializer:
    """
    A class that can serializer an XBlock to OLX
    """
    # TEMP: this needs to be consolidated with the XBlockSerializer in olx_rest_api.
    # i.e. have one base serializer, and a derived blockstore serializer

    def __init__(self, block):
        """
        Serialize an XBlock to an OLX string + supporting files, and store the
        resulting data in this object.
        """
        self.orig_block_key = block.scope_ids.usage_id
        self.static_files = []
        olx_node = self.serialize_block(block)
        self.olx_str = etree.tostring(olx_node, encoding="unicode", pretty_print=True)

        course_key = self.orig_block_key.course_key
        # Search the OLX for references to files stored in the course's
        # "Files & Uploads" (contentstore):
        self.olx_str = adapters.rewrite_absolute_static_urls(self.olx_str, course_key)
        for asset in adapters.collect_assets_from_text(self.olx_str, course_key):
            path = asset['path']
            if path not in [sf.name for sf in self.static_files]:
                self.static_files.append(StaticFile(name=path, url=asset['url'], data=None))

    def serialize_block(self, block) -> etree.Element:
        if self.orig_block_key.block_type == 'html':
            return self.serialize_html_block(block)
        else:
            return self.serialize_normal_block(block)

    def serialize_normal_block(self, block) -> etree.Element:
        """
        Serialize an XBlock to XML.

        This method is used for every block type except HTML, which uses
        serialize_html_block() instead.
        """
        # Create an XML node to hold the exported data
        olx_node = etree.Element("root")  # The node name doesn't matter: add_xml_to_node will change it
        # ^ Note: We could pass nsmap=xblock.core.XML_NAMESPACES here, but the
        # resulting XML namespace attributes don't seem that useful?
        with adapters.override_export_fs(block) as filesystem:  # Needed for XBlocks that inherit XModuleDescriptor
            # Tell the block to serialize itself as XML/OLX:
            if not block.has_children:
                block.add_xml_to_node(olx_node)
            else:
                # We don't want the children serialized at this time, because
                # otherwise we can't tell which files in 'filesystem' belong to
                # this block and which belong to its children. So, temporarily
                # disable any children:
                children = block.children
                block.children = []
                block.add_xml_to_node(olx_node)
                block.children = children

            # Now the block may have exported addtional data as files in
            # 'filesystem'. If so, store them:
            for item in filesystem.walk():  # pylint: disable=not-callable
                for unit_file in item.files:
                    file_path = os.path.join(item.path, unit_file.name)
                    with filesystem.open(file_path, 'rb') as fh:
                        data = fh.read()
                    self.static_files.append(StaticFile(name=unit_file.name, data=data, url=None))
        # Recursively serialize the children:
        if block.has_children:
            for child in block.get_children():
                child_node = self.serialize_block(child)
                olx_node.append(child_node)
        return olx_node

    def serialize_html_block(self, block) -> etree.Element:
        """
        Special case handling for HTML blocks
        """
        olx_node = etree.Element("html")
        if block.display_name:
            olx_node.attrib["display_name"] = block.display_name
        olx_node.text = etree.CDATA("\n" + block.data + "\n")
        return olx_node

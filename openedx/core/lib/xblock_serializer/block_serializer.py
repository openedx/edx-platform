"""
Code for serializing a modulestore XBlock to OLX.
"""
from __future__ import annotations
import logging
import os

from lxml import etree

from openedx.core.djangoapps.content_tagging.api import get_all_object_tags, TagValuesByObjectIdDict

from .data import StaticFile
from . import utils

log = logging.getLogger(__name__)


class XBlockSerializer:
    """
    A class that can serialize an XBlock to OLX.
    """
    static_files: list[StaticFile]
    tags: TagValuesByObjectIdDict

    def __init__(self, block):
        """
        Serialize an XBlock to an OLX string + supporting files, and store the
        resulting data in this object.
        """
        self.orig_block_key = block.scope_ids.usage_id
        self.static_files = []
        self.tags = {}
        olx_node = self._serialize_block(block)
        self.olx_str = etree.tostring(olx_node, encoding="unicode", pretty_print=True)

        course_key = self.orig_block_key.course_key
        # Search the OLX for references to files stored in the course's
        # "Files & Uploads" (contentstore):
        self.olx_str = utils.rewrite_absolute_static_urls(self.olx_str, course_key)

        runtime_supports_explicit_assets = hasattr(block.runtime, 'get_block_assets')
        if runtime_supports_explicit_assets:
            # If a block supports explicitly tracked assets, things are simple.
            # Learning Core backed content supports this, which currently means
            # v2 Content Libraries.
            self.static_files.extend(
                block.runtime.get_block_assets(block)
            )
        else:
            # Otherwise, we have to scan the content to extract associated asset
            # by inference. This is what we have to do for Modulestore-backed
            # courses, which store files a course-global "Files and Uploads".
            for asset in utils.collect_assets_from_text(self.olx_str, course_key):
                path = asset['path']
                if path not in [sf.name for sf in self.static_files]:
                    self.static_files.append(StaticFile(name=path, url=asset['url'], data=None))

            if block.scope_ids.usage_id.block_type in ['problem', 'vertical']:
                py_lib_zip_file = utils.get_python_lib_zip_if_using(self.olx_str, course_key)
                if py_lib_zip_file:
                    self.static_files.append(py_lib_zip_file)

                js_input_files = utils.get_js_input_files_if_using(self.olx_str, course_key)
                for js_input_file in js_input_files:
                    self.static_files.append(js_input_file)

    def _serialize_block(self, block) -> etree.Element:
        """ Serialize an XBlock to OLX/XML. """
        if block.scope_ids.usage_id.block_type == 'html':
            olx = self._serialize_html_block(block)
        else:
            olx = self._serialize_normal_block(block)

        # Store the block's tags
        block_key = block.scope_ids.usage_id
        block_id = str(block_key)
        object_tags, _ = get_all_object_tags(content_key=block_key)
        self.tags[block_id] = object_tags.get(block_id, {})

        return olx

    def _serialize_normal_block(self, block) -> etree.Element:
        """
        Serialize an XBlock to XML.

        This method is used for every block type except HTML, which uses
        serialize_html_block() instead.
        """
        # Create an XML node to hold the exported data
        olx_node = etree.Element("root")  # The node name doesn't matter: add_xml_to_node will change it
        # ^ Note: We could pass nsmap=xblock.core.XML_NAMESPACES here, but the
        # resulting XML namespace attributes don't seem that useful?
        with utils.override_export_fs(block) as filesystem:  # Needed for XBlocks that inherit XModuleDescriptor
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

        if block.has_children:
            self._serialize_children(block, olx_node)

        # Ensure there's a url_name attribute, so we can resurrect child usage keys.
        if "url_name" not in olx_node.attrib:
            olx_node.attrib["url_name"] = block.scope_ids.usage_id.block_id

        return olx_node

    def _serialize_children(self, block, parent_olx_node):
        """
        Recursively serialize the children of XBlock 'block'.
        Subclasses may override this.
        """
        for child in block.get_children():
            child_node = self._serialize_block(child)
            parent_olx_node.append(child_node)

    def _serialize_html_block(self, block) -> etree.Element:
        """
        Special case handling for HTML blocks
        """
        olx_node = etree.Element("html")
        olx_node.attrib["url_name"] = block.scope_ids.usage_id.block_id
        if block.display_name:
            olx_node.attrib["display_name"] = block.display_name
        if block.fields["editor"].is_set_on(block):
            olx_node.attrib["editor"] = block.editor
        if block.use_latex_compiler:
            olx_node.attrib["use_latex_compiler"] = "true"

        # Escape any CDATA special chars
        escaped_block_data = block.data.replace("]]>", "]]&gt;")
        olx_node.text = etree.CDATA(escaped_block_data)
        return olx_node


class XBlockSerializerForLearningCore(XBlockSerializer):
    """
    This class will serialize an XBlock, producing:
        (1) A new definition ID for use in Learning Core
        (2) an XML string defining the XBlock and referencing the IDs of its
            children using <xblock-include /> syntax (which doesn't actually
            contain the OLX of its children, just refers to them, so you have to
            separately serialize them.)
        (3) a list of any static files required by the XBlock and their URL
    """

    def __init__(self, block):
        """
        Serialize an XBlock to an OLX string + supporting files, and store the
        resulting data in this object.
        """
        super().__init__(block)
        self.def_id = utils.learning_core_def_key_from_modulestore_usage_key(self.orig_block_key)

    def _serialize_block(self, block) -> etree.Element:
        """ Serialize an XBlock to OLX/XML. """
        olx_node = super()._serialize_block(block)
        # Apply some transformations to the OLX:
        self._transform_olx(olx_node, usage_id=block.scope_ids.usage_id)
        return olx_node

    def _serialize_children(self, block, parent_olx_node):
        """
        Recursively serialize the children of XBlock 'block'.
        Subclasses may override this.
        """
        for child_id in block.children:
            # In modulestore, the "definition key" is a MongoDB ObjectID
            # kept in split's definitions table, which theoretically allows
            # the same block to be used in many places (each with a unique
            # usage key). However, that functionality is not exposed in
            # Studio (other than via content libraries). So when we import
            # into Learning Core, we assume that each usage is unique, don't
            # generate a usage key, and create a new "definition key" from
            # the original usage key.
            # So modulestore usage key
            #     block-v1:A+B+C+type@html+block@introduction
            # will become Learning Core definition key
            #     html+introduction
            #
            # If we needed the real definition key, we could get it via
            #     child = block.runtime.get_block(child_id)
            #     child_def_id = str(child.scope_ids.def_id)
            # and then use
            #     <xblock-include definition={child_def_id} usage={child_id.block_id} />
            def_id = utils.learning_core_def_key_from_modulestore_usage_key(child_id)
            parent_olx_node.append(parent_olx_node.makeelement("xblock-include", {"definition": def_id}))

    def _transform_olx(self, olx_node, usage_id):
        """
        Apply transformations to the given OLX etree Node.
        """
        # Remove 'url_name' - we store the definition key in the folder name
        # that holds the OLX and the usage key elsewhere, so specifying it
        # within the OLX file is redundant and can lead to issues if the file is
        # copied and pasted elsewhere in the bundle with a new definition key.
        olx_node.attrib.pop('url_name', None)
        # Convert <vertical> to the new <unit> tag/block
        if olx_node.tag == 'vertical':
            olx_node.tag = 'unit'
            for key in olx_node.attrib.keys():
                if key not in ('display_name', 'url_name'):
                    log.warning(
                        '<vertical> tag attribute "%s" will be ignored after conversion to <unit> (in %s)',
                        key,
                        str(usage_id)
                    )

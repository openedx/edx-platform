"""
Code to serialize an XBlock to OLX
"""

from collections import namedtuple
from contextlib import contextmanager
import logging
import os

from fs.memoryfs import MemoryFS
from fs.wrapfs import WrapFS
from lxml.etree import Element
from lxml.etree import tostring as etree_tostring

from xmodule.xml_block import XmlMixin

log = logging.getLogger(__name__)

# A static file required by an XBlock
StaticFile = namedtuple('StaticFile', ['name', 'data'])


def serialize_xblock(block):
    """
    Given an XBlock instance, serialize it to OLX

    Returns
        (olx_str, static_files)
    where olx_str is the XML as a string, and static_files is a list of
    StaticFile objects for any small data files that the XBlock may need for
    complete serialization (e.g. video subtitle files or a .html data file for
    an HTML block).
    """
    static_files = []
    # Create an XML node to hold the exported data
    olx_node = Element("root")  # The node name doesn't matter: add_xml_to_node will change it
    # ^ Note: We could pass nsmap=xblock.core.XML_NAMESPACES here, but the
    # resulting XML namespace attributes don't seem that useful?

    with override_export_fs(block) as filesystem:  # Needed for XBlocks that inherit XModuleDescriptor
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

        # Now the block/module may have exported addtional data as files in
        # 'filesystem'. If so, store them:
        for item in filesystem.walk():  # pylint: disable=not-callable
            for unit_file in item.files:
                file_path = os.path.join(item.path, unit_file.name)
                with filesystem.open(file_path, 'rb') as fh:
                    data = fh.read()
                static_files.append(StaticFile(name=unit_file.name, data=data))

    # Remove 'url_name' - we store the definition key in the folder name
    # that holds the OLX and the usage key elsewhere, so specifying it
    # within the OLX file is redundant and can lead to issues if the file is
    # copied and pasted elsewhere in the bundle with a new definition key.
    olx_node.attrib.pop('url_name', None)

    # Add  <xblock-include /> tags for each child:
    if block.has_children and block.children:
        try:
            child_includes = block.runtime.child_includes_of(block)
        except AttributeError:
            raise RuntimeError("Cannot get child includes of block. Make sure it's using BlockstoreXBlockRuntime")  # lint-amnesty, pylint: disable=raise-missing-from
        if len(child_includes) != len(block.children):
            raise RuntimeError(
                "Mistmatch between block.children and runtime.child_includes_of()."
                "Make sure the block was loaded via runtime.get_block() and that "
                "the block.children field was not modified directly (use "
                "block.runtime.add_child_include() instead)."
            )
        for include_data in child_includes:
            definition_str = include_data.block_type + "/" + include_data.definition_id
            attrs = {"definition": definition_str}
            if include_data.usage_hint:
                attrs["usage"] = include_data.usage_hint
            if include_data.link_id:
                attrs["source"] = include_data.link_id
            olx_node.append(olx_node.makeelement("xblock-include", attrs))

    # Serialize the resulting XML to a string:
    olx_str = etree_tostring(olx_node, encoding="utf-8", pretty_print=True)
    return (olx_str, static_files)


@contextmanager
def override_export_fs(block):
    """
    Hack that makes some legacy XBlocks which inherit `XmlMixin.add_xml_to_node`
    instead of the usual `XmlSerialization.add_xml_to_node` serializable to a string.
    This is needed for the OLX export API.

    Originally, `add_xml_to_node` was `XModuleDescriptor`'s method and was migrated to `XmlMixin`
    as part of the content core platform refactoring. It differs from `XmlSerialization.add_xml_to_node`
    in that it relies on `XmlMixin.export_to_file` (or `CustomTagBlock.export_to_file`) method to control
    whether a block has to be exported as two files (one .olx pointing to one .xml) file, or a single XML node.

    For the legacy blocks (`AnnotatableBlock` for instance) `export_to_file` returns `True` by default.
    The only exception is `CustomTagBlock`, for which this method was originally developed, as customtags don't
    have to be exported as separate files.

    This method temporarily replaces a block's runtime's `export_fs` system with an in-memory filesystem.
    Also, it abuses the `XmlMixin.export_to_file` API to prevent the XBlock export code from exporting
    each block as two files (one .olx pointing to one .xml file).

    Although `XModuleDescriptor` has been removed a long time ago, we have to keep this hack untill the legacy
    `add_xml_to_node` implementation is removed in favor of `XmlSerialization.add_xml_to_node`, which itself
    is a hard task involving refactoring of `CourseExportManager`.
    """
    fs = WrapFS(MemoryFS())
    fs.makedir('course')
    fs.makedir('course/static')  # Video XBlock requires this directory to exists, to put srt files etc.

    old_export_fs = block.runtime.export_fs
    block.runtime.export_fs = fs
    if hasattr(block, 'export_to_file'):
        old_export_to_file = block.export_to_file
        block.export_to_file = lambda: False
    old_global_export_to_file = XmlMixin.export_to_file
    XmlMixin.export_to_file = lambda _: False  # So this applies to child blocks that get loaded during export
    try:
        yield fs
    except:  # lint-amnesty, pylint: disable=try-except-raise
        raise
    finally:
        block.runtime.export_fs = old_export_fs
        if hasattr(block, 'export_to_file'):
            block.export_to_file = old_export_to_file
        XmlMixin.export_to_file = old_global_export_to_file

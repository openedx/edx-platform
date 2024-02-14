"""
Public python API for serializing XBlocks to OLX
"""
# pylint: disable=unused-import
from .block_serializer import StaticFile, XBlockSerializer, XBlockSerializerForBlockstore


def serialize_xblock_to_olx(block):
    """
    This class will serialize an XBlock, producing:
        (1) an XML string defining the XBlock and all of its children (inline)
        (2) a list of any static files required by the XBlock and their URL
    """
    return XBlockSerializer(block)


def serialize_modulestore_block_for_blockstore(block):
    """
    This class will serialize an XBlock, producing:
        (1) A new definition ID for use in Blockstore
        (2) an XML string defining the XBlock and referencing the IDs of its
            children using <xblock-include /> syntax (which doesn't actually
            contain the OLX of its children, just refers to them, so you have to
            separately serialize them.)
        (3) a list of any static files required by the XBlock and their URL

    TODO: We should bring this up to date with Learning Core. I left the name of
    this as-is partly because there are bigger questions that I have around how
    we should alter this (e.g. are we going to remove <xblock-include>?).
    """
    return XBlockSerializerForBlockstore(block)

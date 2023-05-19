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
    """
    return XBlockSerializerForBlockstore(block)

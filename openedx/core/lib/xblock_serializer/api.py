"""
Public python API for serializing XBlocks to OLX
"""
# pylint: disable=unused-import
<<<<<<< HEAD
from .block_serializer import StaticFile, XBlockSerializer, XBlockSerializerForBlockstore
=======
from .block_serializer import StaticFile, XBlockSerializer
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374


def serialize_xblock_to_olx(block):
    """
    This class will serialize an XBlock, producing:
        (1) an XML string defining the XBlock and all of its children (inline)
        (2) a list of any static files required by the XBlock and their URL
<<<<<<< HEAD
=======

    This calls XBlockSerializer with all default options. To actually tweak the
    output, instantiate XBlockSerializer directly.
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    """
    return XBlockSerializer(block)


<<<<<<< HEAD
def serialize_modulestore_block_for_blockstore(block):
    """
    This class will serialize an XBlock, producing:
        (1) A new definition ID for use in Blockstore
=======
def serialize_modulestore_block_for_learning_core(block):
    """
    This class will serialize an XBlock, producing:
        (1) A new definition ID for use in Learning Core
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        (2) an XML string defining the XBlock and referencing the IDs of its
            children using <xblock-include /> syntax (which doesn't actually
            contain the OLX of its children, just refers to them, so you have to
            separately serialize them.)
        (3) a list of any static files required by the XBlock and their URL

    TODO: We should deprecate this in favor of a new Learning Core implementation.
    We've left it as-is for now partly because there are bigger questions that
    we have around how we should rewrite this (e.g. are we going to
    remove <xblock-include>?).
    """
<<<<<<< HEAD
    return XBlockSerializerForBlockstore(block)
=======
    return XBlockSerializer(block, write_url_name=False)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

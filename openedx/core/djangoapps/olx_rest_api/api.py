"""
Public Python API for the OLX REST API app
"""
from .block_serializer import XBlockSerializer as _XBlockSerializer


def serialize_modulestore_block_for_blockstore(block):
    """
    Given a modulestore XBlock (e.g. loaded using
        modulestore.get_item(block_key)
    ), produce:
        (1) A new definition ID for use in Blockstore
        (2) an XML string defining the XBlock and referencing the IDs of its
            children (but not containing the actual XML of its children)
        (3) a list of any static files required by the XBlock and their URL
    """
    return _XBlockSerializer(block)

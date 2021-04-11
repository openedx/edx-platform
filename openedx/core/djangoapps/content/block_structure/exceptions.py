"""
Application-specific exceptions raised by the block structure framework.
"""


class BlockStructureException(Exception):
    """
    Base class for all Block Structure framework exceptions.
    """
    pass


class TransformerException(BlockStructureException):
    """
    Exception class for Transformer related errors.
    """
    pass


class UsageKeyNotInBlockStructure(BlockStructureException):
    """
    Exception for when a usage key is not found within a block structure.
    """
    pass


class TransformerDataIncompatible(BlockStructureException):
    """
    Exception for when the version of a Transformer's data is not
    compatible with the current version of the Transformer.
    """
    pass


class BlockStructureNotFound(BlockStructureException):
    """
    Exception for when a Block Structure is not found.
    """
    def __init__(self, root_block_usage_key):
        super(BlockStructureNotFound, self).__init__(
            u'Block structure not found; data_usage_key: {}'.format(root_block_usage_key)
        )

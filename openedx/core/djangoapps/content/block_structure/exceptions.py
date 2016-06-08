"""
Application-specific exceptions raised by the block structure framework.
"""


class TransformerException(Exception):
    """
    Exception class for Transformer related errors.
    """
    pass


class UsageKeyNotInBlockStructure(Exception):
    """
    Exception for when a usage key is not found within a block structure.
    """
    pass

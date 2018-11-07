"""
A common module for managing exceptions. Helps to avoid circular references
"""


class AssetNotFoundException(Exception):
    """
    Raised when asset not found
    """
    pass


class AssetSizeTooLargeException(Exception):
    """
    Raised when the size of an uploaded asset exceeds the maximum size limit.
    """
    pass

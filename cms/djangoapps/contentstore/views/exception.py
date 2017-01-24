"""
A common module for managing exceptions. Helps to avoid circular references
"""


class AssetNotFoundException(Exception):
    """
    Raised when asset not found
    """
    pass

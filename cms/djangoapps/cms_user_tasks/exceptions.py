"""
Custom exceptions raised by cms user tasks.
"""


class NoAuthHandlerFound(Exception):
    """Is raised when no auth handlers were found ready to authenticate."""
    pass

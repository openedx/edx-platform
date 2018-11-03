# coding: utf-8
"""Open filesystems from a URL.
"""

# Declare fs.opener as a namespace package
__import__("pkg_resources").declare_namespace(__name__)

# Import objects into fs.opener namespace
from .base import Opener
from .parse import parse_fs_url as parse
from .registry import registry

# Alias functions defined as Registry methods
open_fs = registry.open_fs
open = registry.open
manage_fs = registry.manage_fs

# __all__ with aliases and classes
__all__ = ["registry", "Opener", "open_fs", "open", "manage_fs", "parse"]

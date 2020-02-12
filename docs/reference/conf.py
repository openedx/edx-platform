"""
Configuration for the reference documentation.
"""
import sys

from path import Path

root = Path("../..").abspath()
sys.path.insert(0, root)

# pylint: disable=wrong-import-position,redefined-builtin,wildcard-import
from docs.baseconf import *

project = "edx-platform reference manual"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

"""
Contains base test class for nbformat
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import unittest
import io

class TestsBase(unittest.TestCase):
    """Base tests class."""

    def fopen(self, f, mode=u'r',encoding='utf-8'):
        return io.open(os.path.join(self._get_files_path(), f), mode, encoding=encoding)


    def _get_files_path(self):
        return os.path.dirname(__file__)

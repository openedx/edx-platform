# -*- coding: utf-8 -*-
"""
Unit tests for preview.py
"""

import unittest
import preview


class PreviewTest(unittest.TestCase):
    """
    Run tests for preview.latex_preview
    """
    def test_method_works(self):
        """
        Test that no exceptions are thrown and something returns
        """
        result = preview.latex_preview(u"✖^2+1/2")
        self.assertTrue(len(result) > 0)

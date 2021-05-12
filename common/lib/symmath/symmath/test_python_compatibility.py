"""
Tests to check Python syntax
"""

import os
import unittest


class Python35CompatibilityTest(unittest.TestCase):
    """
    Temporary tests to verify that the python syntax is python35 compatible.
    """
    def setUp(self):
        """
        setting up Test environment.
        """
        super().setUp()
        self.module_path = 'common/lib/symmath/symmath/'

    def test_no_fstring_syntax(self):
        """
        Test to verify that no string has the `f-string` syntax
        in it which is incompatible with Python35.
        steps:
        - load file data
        - match for fstring pattern
        - fail the test if fstring pattern matched in any file
        """
        fstring_pattern = "fr?'.*'"
        files = [f for f in os.listdir(self.module_path) if f.endswith('.py') and not f.startswith('test')]
        for file in files:
            file_lines = open(os.path.join(self.module_path, file)).readlines()
            for line in file_lines:
                self.assertNotRegexpMatches(line, fstring_pattern)

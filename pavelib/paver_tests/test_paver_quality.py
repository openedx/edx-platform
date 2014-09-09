import unittest
import pavelib.quality
import tempfile
import os
from ddt import ddt, file_data


@ddt
class TestPaverQualityViolations(unittest.TestCase):

    def setUp(self):
        self.f = tempfile.NamedTemporaryFile(delete=False)
        self.f.close()

    def test_pylint_parser_other_string(self):
        with open(self.f.name, 'w') as f:
            f.write("hello")
        num = pavelib.quality._count_pylint_violations(f.name)
        self.assertEqual(num, 0)

    def test_pylint_parser_pep8(self):
        # Pep8 violations should be ignored.
        with open(self.f.name, 'w') as f:
            f.write("foo/hello/test.py:304:15: E203 whitespace before ':'")
        num = pavelib.quality._count_pylint_violations(f.name)
        self.assertEqual(num, 0)

    @file_data('pylint_test_list.json')
    def test_pylint_parser_count_violations(self, value):
    # Tests:
    #     * Different types of violations
    #     * One violation covering multiple lines
        with open(self.f.name, 'w') as f:
            f.write(value)
        num = pavelib.quality._count_pylint_violations(f.name)
        self.assertEqual(num, 1)

    def test_pep8_parser(self):
        with open(self.f.name, 'w') as f:
            f.write("hello\nhithere")
        num = pavelib.quality._count_pep8_violations(f.name)
        self.assertEqual(num, 2)

    def tearDown(self):
        os.remove(self.f.name)

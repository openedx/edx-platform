"""  # lint-amnesty, pylint: disable=django-not-configured
Tests for paver quality tasks
"""


import os
import shutil  # lint-amnesty, pylint: disable=unused-import
import tempfile
import textwrap
import unittest
from unittest.mock import MagicMock, mock_open, patch  # lint-amnesty, pylint: disable=unused-import

import pytest  # lint-amnesty, pylint: disable=unused-import
from ddt import data, ddt, file_data, unpack  # lint-amnesty, pylint: disable=unused-import
from path import Path as path
from paver.easy import BuildFailure  # lint-amnesty, pylint: disable=unused-import

import pavelib.quality
from pavelib.paver_tests.utils import PaverTestCase, fail_on_eslint  # lint-amnesty, pylint: disable=unused-import

OPEN_BUILTIN = 'builtins.open'


@ddt
class TestPaverQualityViolations(unittest.TestCase):
    """
    For testing the paver violations-counting tasks
    """
    def setUp(self):
        super().setUp()
        self.f = tempfile.NamedTemporaryFile(delete=False)  # lint-amnesty, pylint: disable=consider-using-with
        self.f.close()
        self.addCleanup(os.remove, self.f.name)

    def test_pylint_parser_other_string(self):
        with open(self.f.name, 'w') as f:
            f.write("hello")
        num = pavelib.quality._count_pylint_violations(f.name)  # pylint: disable=protected-access
        assert num == 0

    def test_pylint_parser_pep8(self):
        # Pep8 violations should be ignored.
        with open(self.f.name, 'w') as f:
            f.write("foo/hello/test.py:304:15: E203 whitespace before ':'")
        num = pavelib.quality._count_pylint_violations(f.name)  # pylint: disable=protected-access
        assert num == 0

    @file_data('pylint_test_list.json')
    def test_pylint_parser_count_violations(self, value):
        """
        Tests:
        - Different types of violations
        - One violation covering multiple lines
        """
        with open(self.f.name, 'w') as f:
            f.write(value)
        num = pavelib.quality._count_pylint_violations(f.name)  # pylint: disable=protected-access
        assert num == 1

    def test_pep8_parser(self):
        with open(self.f.name, 'w') as f:
            f.write("hello\nhithere")
        num = len(pavelib.quality._pep8_violations(f.name))  # pylint: disable=protected-access
        assert num == 2


class TestPaverReportViolationsCounts(unittest.TestCase):
    """
    For testing utility functions for getting counts from reports for
    run_eslint and run_xsslint.
    """

    def setUp(self):
        super().setUp()

        # Temporary file infrastructure
        self.f = tempfile.NamedTemporaryFile(delete=False)  # lint-amnesty, pylint: disable=consider-using-with
        self.f.close()

        # Cleanup various mocks and tempfiles
        self.addCleanup(os.remove, self.f.name)

    def test_get_eslint_violations_count(self):
        with open(self.f.name, 'w') as f:
            f.write("3000 violations found")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name, "eslint")  # pylint: disable=protected-access
        assert actual_count == 3000

    def test_get_eslint_violations_no_number_found(self):
        with open(self.f.name, 'w') as f:
            f.write("Not expected string regex")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name, "eslint")  # pylint: disable=protected-access
        assert actual_count is None

    def test_get_eslint_violations_count_truncated_report(self):
        """
        A truncated report (i.e. last line is just a violation)
        """
        with open(self.f.name, 'w') as f:
            f.write("foo/bar/js/fizzbuzz.js: line 45, col 59, Missing semicolon.")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name, "eslint")  # pylint: disable=protected-access
        assert actual_count is None

    def test_generic_value(self):
        """
        Default behavior is to look for an integer appearing at head of line
        """
        with open(self.f.name, 'w') as f:
            f.write("5.777 good to see you")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name, "foo")  # pylint: disable=protected-access
        assert actual_count == 5

    def test_generic_value_none_found(self):
        """
        Default behavior is to look for an integer appearing at head of line
        """
        with open(self.f.name, 'w') as f:
            f.write("hello 5.777 good to see you")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name, "foo")  # pylint: disable=protected-access
        assert actual_count is None

    def test_get_xsslint_counts_happy(self):
        """
        Test happy path getting violation counts from xsslint report.
        """
        report = textwrap.dedent("""
            test.html: 30:53: javascript-jquery-append:  $('#test').append(print_tos);

            javascript-concat-html: 310 violations
            javascript-escape:      7 violations

            2608 violations total
        """)
        with open(self.f.name, 'w') as f:
            f.write(report)
        counts = pavelib.quality._get_xsslint_counts(self.f.name)  # pylint: disable=protected-access
        self.assertDictEqual(counts, {
            'rules': {
                'javascript-concat-html': 310,
                'javascript-escape': 7,
            },
            'total': 2608,
        })

    def test_get_xsslint_counts_bad_counts(self):
        """
        Test getting violation counts from truncated and malformed xsslint
        report.
        """
        report = textwrap.dedent("""
            javascript-concat-html: violations
        """)
        with open(self.f.name, 'w') as f:
            f.write(report)
        counts = pavelib.quality._get_xsslint_counts(self.f.name)  # pylint: disable=protected-access
        self.assertDictEqual(counts, {
            'rules': {},
            'total': None,
        })


class TestPrepareReportDir(unittest.TestCase):
    """
    Tests the report directory preparation
    """

    def setUp(self):
        super().setUp()
        self.test_dir = tempfile.mkdtemp()
        self.test_file = tempfile.NamedTemporaryFile(delete=False, dir=self.test_dir)  # lint-amnesty, pylint: disable=consider-using-with
        self.addCleanup(os.removedirs, self.test_dir)

    def test_report_dir_with_files(self):
        assert os.path.exists(self.test_file.name)
        pavelib.quality._prepare_report_dir(path(self.test_dir))  # pylint: disable=protected-access
        assert not os.path.exists(self.test_file.name)

    def test_report_dir_without_files(self):
        os.remove(self.test_file.name)
        pavelib.quality._prepare_report_dir(path(self.test_dir))  # pylint: disable=protected-access
        assert os.listdir(path(self.test_dir)) == []

"""
Tests for paver quality tasks
"""


import os
import shutil
import tempfile
import textwrap
import unittest

from ddt import data, ddt, file_data, unpack
from mock import MagicMock, mock_open, patch
from path import Path as path
from paver.easy import BuildFailure

import pavelib.quality
from pavelib.paver_tests.utils import PaverTestCase, fail_on_eslint

OPEN_BUILTIN = 'builtins.open'


@ddt
class TestPaverQualityViolations(unittest.TestCase):
    """
    For testing the paver violations-counting tasks
    """
    def setUp(self):
        super().setUp()
        self.f = tempfile.NamedTemporaryFile(delete=False)
        self.f.close()
        self.addCleanup(os.remove, self.f.name)

    def test_pylint_parser_other_string(self):
        with open(self.f.name, 'w') as f:
            f.write("hello")
        num = pavelib.quality._count_pylint_violations(f.name)  # pylint: disable=protected-access
        self.assertEqual(num, 0)

    def test_pylint_parser_pep8(self):
        # Pep8 violations should be ignored.
        with open(self.f.name, 'w') as f:
            f.write("foo/hello/test.py:304:15: E203 whitespace before ':'")
        num = pavelib.quality._count_pylint_violations(f.name)  # pylint: disable=protected-access
        self.assertEqual(num, 0)

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
        self.assertEqual(num, 1)

    def test_pep8_parser(self):
        with open(self.f.name, 'w') as f:
            f.write("hello\nhithere")
        num = len(pavelib.quality._pep8_violations(f.name))  # pylint: disable=protected-access
        self.assertEqual(num, 2)


@ddt
class TestPaverQualityOptions(unittest.TestCase):
    """
    Tests the paver pylint command-line options parsing.
    """
    @data(
        ({'limit': '5500'}, (-1, 5500, False, pavelib.quality.ALL_SYSTEMS.split(','))),
        ({'limit': '1000:5500'}, (1000, 5500, False, pavelib.quality.ALL_SYSTEMS.split(','))),
        ({'limit': '1:2:3:4:5'}, (1, 2, False, pavelib.quality.ALL_SYSTEMS.split(','))),
        ({'system': 'lms,cms'}, (-1, -1, False, ['lms', 'cms'])),
        (
            {'limit': '2000:5000', 'errors': True, 'system': 'lms,cms,openedx'},
            (2000, 5000, True, ['lms', 'cms', 'openedx'])
        ),
    )
    @unpack
    def test_pylint_parser_other_string(self, options, expected_values):
        class PaverOptions:
            """
            Simple options class to mimick paver's Namespace object.
            """
            def __init__(self, d):
                self.__dict__ = d
        paver_options = PaverOptions(options)
        returned_values = pavelib.quality._parse_pylint_options(paver_options)  # pylint: disable=protected-access
        self.assertEqual(returned_values, expected_values)


class TestPaverReportViolationsCounts(unittest.TestCase):
    """
    For testing utility functions for getting counts from reports for
    run_eslint, run_xsslint, and run_xsscommitlint.
    """

    def setUp(self):
        super().setUp()

        # Temporary file infrastructure
        self.f = tempfile.NamedTemporaryFile(delete=False)
        self.f.close()

        # Cleanup various mocks and tempfiles
        self.addCleanup(os.remove, self.f.name)

    def test_get_eslint_violations_count(self):
        with open(self.f.name, 'w') as f:
            f.write("3000 violations found")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name, "eslint")  # pylint: disable=protected-access
        self.assertEqual(actual_count, 3000)

    def test_get_eslint_violations_no_number_found(self):
        with open(self.f.name, 'w') as f:
            f.write("Not expected string regex")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name, "eslint")  # pylint: disable=protected-access
        self.assertEqual(actual_count, None)

    def test_get_eslint_violations_count_truncated_report(self):
        """
        A truncated report (i.e. last line is just a violation)
        """
        with open(self.f.name, 'w') as f:
            f.write("foo/bar/js/fizzbuzz.js: line 45, col 59, Missing semicolon.")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name, "eslint")  # pylint: disable=protected-access
        self.assertEqual(actual_count, None)

    def test_generic_value(self):
        """
        Default behavior is to look for an integer appearing at head of line
        """
        with open(self.f.name, 'w') as f:
            f.write("5.777 good to see you")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name, "foo")  # pylint: disable=protected-access
        self.assertEqual(actual_count, 5)

    def test_generic_value_none_found(self):
        """
        Default behavior is to look for an integer appearing at head of line
        """
        with open(self.f.name, 'w') as f:
            f.write("hello 5.777 good to see you")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name, "foo")  # pylint: disable=protected-access
        self.assertEqual(actual_count, None)

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

    def test_get_xsscommitlint_count_happy(self):
        """
        Test happy path getting violation count from xsscommitlint report.
        """
        report = textwrap.dedent("""
            Linting lms/templates/navigation.html:

            2 violations total

            Linting scripts/tests/templates/test.underscore:

            3 violations total
        """)
        with open(self.f.name, 'w') as f:
            f.write(report)
        count = pavelib.quality._get_xsscommitlint_count(self.f.name)  # pylint: disable=protected-access

        self.assertEqual(count, 5)

    def test_get_xsscommitlint_count_bad_counts(self):
        """
        Test getting violation count from truncated xsscommitlint report.
        """
        report = textwrap.dedent("""
            Linting lms/templates/navigation.html:
        """)
        with open(self.f.name, 'w') as f:
            f.write(report)
        count = pavelib.quality._get_xsscommitlint_count(self.f.name)  # pylint: disable=protected-access

        self.assertIsNone(count)

    def test_get_xsscommitlint_count_no_files(self):
        """
        Test getting violation count from xsscommitlint report where no files were
        linted.
        """
        report = textwrap.dedent("""
            No files linted.
        """)
        with open(self.f.name, 'w') as f:
            f.write(report)
        count = pavelib.quality._get_xsscommitlint_count(self.f.name)  # pylint: disable=protected-access

        self.assertEqual(count, 0)


class TestPrepareReportDir(unittest.TestCase):
    """
    Tests the report directory preparation
    """

    def setUp(self):
        super().setUp()
        self.test_dir = tempfile.mkdtemp()
        self.test_file = tempfile.NamedTemporaryFile(delete=False, dir=self.test_dir)
        self.addCleanup(os.removedirs, self.test_dir)

    def test_report_dir_with_files(self):
        self.assertTrue(os.path.exists(self.test_file.name))
        pavelib.quality._prepare_report_dir(path(self.test_dir))  # pylint: disable=protected-access
        self.assertFalse(os.path.exists(self.test_file.name))

    def test_report_dir_without_files(self):
        os.remove(self.test_file.name)
        pavelib.quality._prepare_report_dir(path(self.test_dir))  # pylint: disable=protected-access
        self.assertEqual(os.listdir(path(self.test_dir)), [])


class TestPaverRunQuality(PaverTestCase):
    """
    For testing the paver run_quality task
    """

    def setUp(self):
        super().setUp()

        # mock the @needs decorator to skip it
        patcher = patch('pavelib.quality.sh')
        self._mock_paver_sh = patcher.start()
        self.addCleanup(patcher.stop)

        self.report_dir = tempfile.mkdtemp()
        report_dir_patcher = patch('pavelib.utils.envs.Env.REPORT_DIR', path(self.report_dir))
        report_dir_patcher.start()
        self.addCleanup(shutil.rmtree, self.report_dir)
        self.addCleanup(report_dir_patcher.stop)

    @patch(OPEN_BUILTIN, mock_open())
    def test_failure_on_diffquality_pylint(self):
        """
        If diff-quality fails on pylint, the paver task should also fail, but
        only after runnning diff-quality with eslint
        """

        # Underlying sh call must fail when it is running the pylint diff-quality task
        _mock_pylint_violations = MagicMock(return_value=(10000, ['some error']))
        with patch('pavelib.quality._get_pylint_violations', _mock_pylint_violations):
            with patch('pavelib.quality._parse_pylint_options', return_value=(0, 1000, 0, 0)):
                with self.assertRaises(SystemExit):
                    pavelib.quality.run_quality("")

        # Assert that _get_pylint_violations (which calls "pylint") is called once
        self.assertEqual(_mock_pylint_violations.call_count, 1)
        # Assert that sh was called twice- once for diff quality with pylint
        # and once for diff quality with eslint. This means that in the event
        # of a diff-quality pylint failure, eslint is still called.
        self.assertEqual(self._mock_paver_sh.call_count, 2)

    @patch(OPEN_BUILTIN, mock_open())
    def test_failure_on_diffquality_eslint(self):
        """
        If diff-quality fails on eslint, the paver task should also fail
        """
        # Underlying sh call must fail when it is running the eslint diff-quality task
        self._mock_paver_sh.side_effect = fail_on_eslint
        _mock_pylint_violations = MagicMock(return_value=(0, []))
        with patch('pavelib.quality._get_pylint_violations', _mock_pylint_violations):
            with self.assertRaises(SystemExit):
                pavelib.quality.run_quality("")
        print(self._mock_paver_sh.mock_calls)

        # Test that pylint is called
        _mock_pylint_violations.assert_called_once_with(clean=False)
        # Assert that sh was called four times - once to get the comparison commit hash,
        # once to get the current commit hash, once for diff quality with pylint,
        # and once for diff quality with eslint
        self.assertEqual(self._mock_paver_sh.call_count, 4)

    @patch(OPEN_BUILTIN, mock_open())
    def test_other_exception(self):
        """
        If diff-quality fails for an unknown reason on the first run, then
        pylint should not be run
        """
        self._mock_paver_sh.side_effect = [Exception('unrecognized failure!'), 0]
        with self.assertRaises(SystemExit):
            pavelib.quality.run_quality("")
        # Test that pylint is NOT called by counting calls
        self.assertEqual(self._mock_paver_sh.call_count, 1)

    @patch(OPEN_BUILTIN, mock_open())
    def test_no_diff_quality_failures(self):
        # Assert nothing is raised
        pavelib.quality.run_quality("")
        # And assert that sh was called 8 times:
        # 6 for pylint on each of the system directories
        # 1 for diff_quality for pylint
        # 1 for diff_quality for eslint
        self.assertEqual(self._mock_paver_sh.call_count, 8)


class TestPaverRunDiffQuality(PaverTestCase):
    """
    For testing the paver run_diff_quality task

    Note: Although diff_quality is tested as part of quality, some
    cases weren't tested properly.
    """
    def setUp(self):
        super().setUp()

        # mock the @needs decorator to skip it
        patcher = patch('pavelib.quality.sh')
        self._mock_paver_sh = patcher.start()
        self.addCleanup(patcher.stop)

    @patch(OPEN_BUILTIN, mock_open())
    def test_percentage_failure(self):
        """
        When diff_quality is run with a threshold percentage, it ends with an exit code of 1.
        This bubbles up to paver with a subprocess return code error and should return False.
        """
        self._mock_paver_sh.side_effect = [BuildFailure('Subprocess return code: 1')]
        self.assertEqual(pavelib.quality.run_diff_quality(""), False)

    @patch(OPEN_BUILTIN, mock_open())
    def test_other_failures(self):
        """
        Run diff_quality with an exception that is not a percentage failure.
        """
        self._mock_paver_sh.side_effect = [BuildFailure('Some failure.')]
        with self.assertRaisesRegex(BuildFailure, '.*Diff Quality Report.*Some failure.'):
            pavelib.quality.run_diff_quality("")

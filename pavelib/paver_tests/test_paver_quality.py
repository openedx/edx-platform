"""
Tests for paver quality tasks
"""
import os
from path import path  # pylint: disable=no-name-in-module
import tempfile
import unittest
from mock import patch, MagicMock, mock_open
from ddt import ddt, file_data

import pavelib.quality
import paver.easy
import paver.tasks
from paver.easy import BuildFailure


@ddt
class TestPaverQualityViolations(unittest.TestCase):
    """
    For testing the paver violations-counting tasks
    """
    def setUp(self):
        super(TestPaverQualityViolations, self).setUp()
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
        num, _violations = pavelib.quality._pep8_violations(f.name)  # pylint: disable=protected-access
        self.assertEqual(num, 2)


class TestPaverJsHintViolationsCounts(unittest.TestCase):
    """
    For testing run_jshint
    """

    def setUp(self):
        super(TestPaverJsHintViolationsCounts, self).setUp()

        # Mock the paver @needs decorator
        self._mock_paver_needs = patch.object(pavelib.quality.run_quality, 'needs').start()
        self._mock_paver_needs.return_value = 0

        # Temporary file infrastructure
        self.f = tempfile.NamedTemporaryFile(delete=False)
        self.f.close()

        # Cleanup various mocks and tempfiles
        self.addCleanup(self._mock_paver_needs.stop)
        self.addCleanup(os.remove, self.f.name)

    def test_get_violations_count(self):
        with open(self.f.name, 'w') as f:
            f.write("3000 violations found")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name)  # pylint: disable=protected-access
        self.assertEqual(actual_count, 3000)

    def test_get_violations_no_number_found(self):
        with open(self.f.name, 'w') as f:
            f.write("Not expected string regex")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name)  # pylint: disable=protected-access
        self.assertEqual(actual_count, None)

    def test_get_violations_count_truncated_report(self):
        """
        A truncated report (i.e. last line is just a violation)
        """
        with open(self.f.name, 'w') as f:
            f.write("foo/bar/js/fizzbuzz.js: line 45, col 59, Missing semicolon.")
        actual_count = pavelib.quality._get_count_from_last_line(self.f.name)  # pylint: disable=protected-access
        self.assertEqual(actual_count, None)


class TestPrepareReportDir(unittest.TestCase):
    """
    Tests the report directory preparation
    """

    def setUp(self):
        super(TestPrepareReportDir, self).setUp()
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


class TestPaverRunQuality(unittest.TestCase):
    """
    For testing the paver run_quality task
    """

    def setUp(self):
        super(TestPaverRunQuality, self).setUp()

        # test_no_diff_quality_failures seems to alter the way that paver
        # executes these lines is subsequent tests.
        # https://github.com/paver/paver/blob/master/paver/tasks.py#L175-L180
        #
        # The other tests don't appear to have the same impact. This was
        # causing a test order dependency. This line resets that state
        # of environment._task_in_progress so that the paver commands in the
        # tests will be considered top level tasks by paver, and we can predict
        # which path it will chose in the above code block.
        #
        # TODO: Figure out why one test is altering the state to begin with.
        paver.tasks.environment = paver.tasks.Environment()

        # mock the @needs decorator to skip it
        self._mock_paver_needs = patch.object(pavelib.quality.run_quality, 'needs').start()
        self._mock_paver_needs.return_value = 0
        patcher = patch('pavelib.quality.sh')
        self._mock_paver_sh = patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._mock_paver_needs.stop)

    @patch('__builtin__.open', mock_open())
    def test_failure_on_diffquality_pep8(self):
        """
        If pep8 finds errors, pylint should still be run
        """
        # Mock _get_pep8_violations to return a violation
        _mock_pep8_violations = MagicMock(
            return_value=(1, ['lms/envs/common.py:32:2: E225 missing whitespace around operator'])
        )
        with patch('pavelib.quality._get_pep8_violations', _mock_pep8_violations):
            with self.assertRaises(SystemExit):
                pavelib.quality.run_quality("")
                self.assertRaises(BuildFailure)

        # Test that both pep8 and pylint were called by counting the calls to _get_pep8_violations
        # (for pep8) and sh (for diff-quality pylint)
        self.assertEqual(_mock_pep8_violations.call_count, 1)
        self.assertEqual(self._mock_paver_sh.call_count, 1)

    @patch('__builtin__.open', mock_open())
    def test_failure_on_diffquality_pylint(self):
        """
        If diff-quality fails on pylint, the paver task should also fail
        """

        # Underlying sh call must fail when it is running the pylint diff-quality task
        self._mock_paver_sh.side_effect = CustomShMock().fail_on_pylint
        _mock_pep8_violations = MagicMock(return_value=(0, []))
        with patch('pavelib.quality._get_pep8_violations', _mock_pep8_violations):
            with self.assertRaises(SystemExit):
                pavelib.quality.run_quality("")
                self.assertRaises(BuildFailure)
        # Test that both pep8 and pylint were called by counting the calls
        # Assert that _get_pep8_violations (which calls "pep8") is called once
        self.assertEqual(_mock_pep8_violations.call_count, 1)
        # And assert that sh was called once (for the call to "pylint")
        self.assertEqual(self._mock_paver_sh.call_count, 1)

    @patch('__builtin__.open', mock_open())
    def test_other_exception(self):
        """
        If diff-quality fails for an unknown reason on the first run (pep8), then
        pylint should not be run
        """
        self._mock_paver_sh.side_effect = [Exception('unrecognized failure!'), 0]
        with self.assertRaises(SystemExit):
            pavelib.quality.run_quality("")
            self.assertRaises(Exception)
        # Test that pylint is NOT called by counting calls
        self.assertEqual(self._mock_paver_sh.call_count, 1)

    @patch('__builtin__.open', mock_open())
    def test_no_diff_quality_failures(self):
        # Assert nothing is raised
        _mock_pep8_violations = MagicMock(return_value=(0, []))
        with patch('pavelib.quality._get_pep8_violations', _mock_pep8_violations):
            pavelib.quality.run_quality("")
        # Assert that _get_pep8_violations (which calls "pep8") is called once
        self.assertEqual(_mock_pep8_violations.call_count, 1)
        # And assert that sh was called once (for the call to "pylint")
        self.assertEqual(self._mock_paver_sh.call_count, 1)


class CustomShMock(object):
    """
    Diff-quality makes a number of sh calls. None of those calls should be made during tests; however, some
    of them need to have certain responses.
    """

    def fail_on_pylint(self, arg):
        """
        For our tests, we need the call for diff-quality running pep8 reports to fail, since that is what
        is going to fail when we pass in a percentage ("p") requirement.
        """
        if "pylint" in arg:
            # Essentially mock diff-quality exiting with 1
            paver.easy.sh("exit 1")
        else:
            return

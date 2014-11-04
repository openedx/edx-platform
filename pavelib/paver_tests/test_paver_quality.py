import os
import tempfile
import unittest
from mock import patch
from ddt import ddt, file_data

import pavelib.quality
import paver.easy
from paver.easy import BuildFailure

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


class TestPaverRunQuality(unittest.TestCase):
    """
    For testing the paver run_quality task
    """

    def setUp(self):

        # mock the @needs decorator to skip it
        self._mock_paver_needs = patch.object(pavelib.quality.run_quality, 'needs').start()
        self._mock_paver_needs.return_value = 0
        self._mock_paver_sh = patch('pavelib.quality.sh').start()

    def test_failure_on_diffquality_pep8(self):
        """
       If pep8 diff-quality fails due to the percentage threshold, pylint
       should still be run
        """

        # Underlying sh call must fail when it is running the pep8 diff-quality task
        self._mock_paver_sh.side_effect = CustomShMock().fail_on_pep8
        with self.assertRaises(SystemExit):
            pavelib.quality.run_quality("")
            self.assertRaises(BuildFailure)
        # Test that both pep8 and pylint were called by counting the calls
        self.assertEqual(self._mock_paver_sh.call_count, 2)

    def test_failure_on_diffquality_pylint(self):
        """
        If diff-quality fails on pylint, the paver task should also fail
        """

        # Underlying sh call must fail when it is running the pylint diff-quality task
        self._mock_paver_sh.side_effect = CustomShMock().fail_on_pylint
        with self.assertRaises(SystemExit):
            pavelib.quality.run_quality("")
            self.assertRaises(BuildFailure)
        # Test that both pep8 and pylint were called by counting the calls
        self.assertEqual(self._mock_paver_sh.call_count, 2)

    def test_other_exception(self):
        """
        If diff-quality fails for an unknown reason on the first run (pep8), then
        pylint should not be run
        """
        self._mock_paver_sh.side_effect = [Exception('unrecognized failure!'), 0]
        with self.assertRaises(Exception):
            pavelib.quality.run_quality("")
        # Test that pylint is NOT called by counting calls
        self.assertEqual(self._mock_paver_sh.call_count, 1)

    def test_no_diff_quality_failures(self):
        # Assert nothing is raised
        pavelib.quality.run_quality("")
        self.assertEqual(self._mock_paver_sh.call_count, 2)


class CustomShMock(object):
    """
    Diff-quality makes a number of sh calls. None of those calls should be made during tests; however, some
    of them need to have certain responses.
    """

    def fail_on_pep8(self, arg):
        """
        For our tests, we need the call for diff-quality running pep8 reports to fail, since that is what
        is going to fail when we pass in a percentage ("p") requirement.
        """
        if "pep8" in arg:
            # Essentially mock diff-quality exiting with 1
            paver.easy.sh("exit 1")
        else:
            return

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

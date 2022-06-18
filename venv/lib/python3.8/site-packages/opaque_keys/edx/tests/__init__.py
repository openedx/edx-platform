"""
Utilities for other Location tests to use
"""
import warnings
from contextlib import contextmanager
from unittest import TestCase


class TestDeprecated(TestCase):
    """Base class (with utility methods) for deprecated Location tests"""
    def setUp(self):
        super().setUp()

        # Manually invoke the catch_warnings context manager so we can capture DeprecationWarnings
        # during this test run
        self.cws = warnings.catch_warnings()
        self.cws.__enter__()
        # Python 2.7 by default suppresses DeprecationWarnings. Make sure we show these, always, during tests.
        warnings.simplefilter('always', DeprecationWarning)

        # Manually exit the catch_warnings context manager when the test is done
        self.addCleanup(self.cws.__exit__)

    @contextmanager
    def assertDeprecationWarning(self, count=1):
        """Asserts that the contained code raises `count` deprecation warnings"""
        with warnings.catch_warnings(record=True) as caught:
            yield
        self.assertEqual(count,
                         len([warning for warning in caught if issubclass(warning.category, DeprecationWarning)]))


class LocatorBaseTest(TestCase):
    """
    Utilities used in other Location tests
    """
    # ------------------------------------------------------------------
    # Utilities

    def check_course_locn_fields(self, testobj, version_guid=None,
                                 org=None, course=None, run=None, branch=None):
        """
        Checks the version, org, course, run, and branch in testobj
        """
        self.assertEqual(testobj.version_guid, version_guid)
        self.assertEqual(testobj.org, org)
        self.assertEqual(testobj.course, course)
        self.assertEqual(testobj.run, run)
        self.assertEqual(testobj.branch, branch)

    def check_block_locn_fields(self, testobj, version_guid=None,
                                org=None, course=None, run=None, branch=None, block_type=None, block=None):
        """
        Does adds a block id check over and above the check_course_locn_fields tests
        """
        self.check_course_locn_fields(testobj, version_guid, org, course, run,
                                      branch)
        if block_type is not None:
            self.assertEqual(testobj.block_type, block_type)
        self.assertEqual(testobj.block_id, block)

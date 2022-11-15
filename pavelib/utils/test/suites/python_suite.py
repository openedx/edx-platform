"""
Classes used for defining and running python test suites
"""


import os

from pavelib.utils.envs import Env
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites.pytest_suite import LibTestSuite, SystemTestSuite
from pavelib.utils.test.suites.suite import TestSuite

__test__ = False  # do not collect


class PythonTestSuite(TestSuite):
    """
    A subclass of TestSuite with extra setup for python tests
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.opts = kwargs
        self.disable_migrations = kwargs.get('disable_migrations', True)
        self.fasttest = kwargs.get('fasttest', False)
        self.subsuites = kwargs.get('subsuites', self._default_subsuites)

    def __enter__(self):
        super().__enter__()

        if self.disable_migrations:
            os.environ['DISABLE_MIGRATIONS'] = '1'

        if not (self.fasttest or self.skip_clean):
            test_utils.clean_test_files()

    @property
    def _default_subsuites(self):
        """
        The default subsuites to be run. They include lms, cms,
        and all of the libraries in pavelib/paver_tests.
        """
        lib_suites = [
            LibTestSuite(d, **self.opts) for d in Env.LIB_TEST_DIRS
        ]

        system_suites = [
            SystemTestSuite('cms', **self.opts),
            SystemTestSuite('lms', **self.opts),
        ]

        return system_suites + lib_suites

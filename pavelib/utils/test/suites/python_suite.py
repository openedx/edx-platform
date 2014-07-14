"""
Classes used for defining and running python test suites
"""
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites import TestSuite, LibTestSuite, SystemTestSuite
from pavelib.utils.envs import Env

__test__ = False  # do not collect


class PythonTestSuite(TestSuite):
    """
    A subclass of TestSuite with extra setup for python tests
    """
    def __init__(self, *args, **kwargs):
        super(PythonTestSuite, self).__init__(*args, **kwargs)
        self.fasttest = kwargs.get('fasttest', False)
        self.failed_only = kwargs.get('failed_only', None)
        self.fail_fast = kwargs.get('fail_fast', None)
        self.subsuites = kwargs.get('subsuites', self._default_subsuites)

    def __enter__(self):
        super(PythonTestSuite, self).__enter__()
        if not self.fasttest:
            test_utils.clean_test_files()

    @property
    def _default_subsuites(self):
        """
        The default subsuites to be run. They include lms, cms,
        and all of the libraries in common/lib.
        """
        opts = {
            'failed_only': self.failed_only,
            'fail_fast': self.fail_fast,
            'fasttest': self.fasttest,
        }

        lib_suites = [
            LibTestSuite(d, **opts) for d in Env.LIB_TEST_DIRS
        ]

        system_suites = [
            SystemTestSuite('cms', **opts),
            SystemTestSuite('lms', **opts),
        ]

        return system_suites + lib_suites

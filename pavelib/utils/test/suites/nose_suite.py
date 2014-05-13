"""
Classes used for defining and running nose test suites
"""
import os
from paver.easy import call_task
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites import TestSuite
from pavelib.utils.envs import Env

__test__ = False  # do not collect


class NoseTestSuite(TestSuite):
    """
    A subclass of TestSuite with extra methods that are specific to nose tests
    """
    def __init__(self, *args, **kwargs):
        super(NoseTestSuite, self).__init__(*args, **kwargs)
        self.failed_only = kwargs.get('failed_only', False)
        self.fail_fast = kwargs.get('fail_fast', False)
        self.report_dir, self.test_id_dir, self.test_ids = self._required_dirs()

    @property
    def under_coverage_cmd(self):
        cmd0, cmd_rest = self.cmd.split(" ", 1)
        # We use "python -m coverage" so that the proper python will run the importable coverage
        # rather than the coverage that OS path finds.

        cmd = "python -m coverage run --rcfile={root}/.coveragerc `which {cmd0}` {cmd_rest}".format(
            root=self.root, cmd0=cmd0, cmd_rest=cmd_rest)

        return cmd

    @property
    def test_options_flags(self):
        """
        Takes the test options and returns the appropriate flags for the command.
        """
        opts = " "

        # Handle "--failed" as a special case: we want to re-run only
        # the tests that failed within our Django apps
        # This sets the --failed flag for the nosetests command, so this
        # functionality is the same as described in the nose documentation
        if self.failed_only:
            opts += "--failed"

        # This makes it so we use nose's fail-fast feature in two cases.
        # Case 1: --fail_fast is passed as an arg in the paver command
        # Case 2: The environment variable TESTS_FAIL_FAST is set as True
        if self.fail_fast or ('TESTS_FAIL_FAST' in os.environ and os.environ['TEST_FAIL_FAST']):
            opts += " --stop"

        return opts

    def _clean_up(self):
        """
        Cleans mongo afer the tests run.
        """
        test_utils.clean_mongo()

    def _required_dirs(self):
        """
        Makes sure that the reports directory and the nodeids
        directory are present.
        """
        report_dir = test_utils.get_or_make_dir(
            os.path.join(Env.REPORT_DIR, self.root)
        )

        test_id_dir = test_utils.get_or_make_dir(
            os.path.join(Env.TEST_DIR, self.root)
        )

        # no need to create test_ids file, since nose will do that
        test_ids = os.path.join(test_id_dir, 'noseids')

        return report_dir, test_id_dir, test_ids


class SystemTestSuite(NoseTestSuite):
    """
    TestSuite for lms and cms nosetests
    """
    def __init__(self, *args, **kwargs):
        super(SystemTestSuite, self).__init__(*args, **kwargs)
        self.test_id = kwargs.get('test_id', self._default_test_id)
        self.fasttest = kwargs.get('fasttest', False)
        self.run_under_coverage = kwargs.get('with_coverage', True)

    @property
    def cmd(self):
        cmd = './manage.py {system} test {test_id} {test_opts} --traceback --settings=test'.format(
            system=self.root, test_id=self.test_id, test_opts=self.test_options_flags)
        return cmd

    @property
    def _default_test_id(self):
        """
        If no test id is provided, we need to limit the test runner
        to the Djangoapps we want to test.  Otherwise, it will
        run tests on all installed packages. We do this by
        using a default test id.
        """
        # We need to use $DIR/*, rather than just $DIR so that
        # django-nose will import them early in the test process,
        # thereby making sure that we load any django models that are
        # only defined in test files.
        default_test_id = "{system}/djangoapps/* common/djangoapps/*".format(system=self.root)

        if self.root in ('lms', 'cms'):
            default_test_id += " {system}/lib/*".format(system=self.root)

        if self.root == 'lms':
            default_test_id += " {system}/tests.py".format(system=self.root)

        return default_test_id

    def _set_up(self):
        super(SystemTestSuite, self)._set_up()
        if not self.fasttest:
            # TODO: Fix the tests so that collectstatic isn't needed ever
            # add --skip-collect to this when the tests are fixed
            args = [self.root, '--settings=test']
            call_task('pavelib.assets.update_assets', args=args)


class LibTestSuite(NoseTestSuite):
    """
    TestSuite for edx-platform/common/lib nosetests
    """
    def __init__(self, *args, **kwargs):
        super(LibTestSuite, self).__init__(*args, **kwargs)
        self.test_id = kwargs.get('test_id', self.root)
        self.run_under_coverage = kwargs.get('with_coverage', True)

    @property
    def cmd(self):
        cmd = "nosetests --id-file={test_ids} {test_id} {test_opts}".format(
            test_ids=self.test_ids, test_id=self.test_id, test_opts=self.test_options_flags)

        return cmd

    def _set_up(self):
        super(LibTestSuite, self)._set_up()
        if os.path.exists(os.path.join(self.report_dir, "nosetests.xml")):
            os.environ['NOSE_XUNIT_FILE'] = os.path.join(self.report_dir, "nosetests.xml")

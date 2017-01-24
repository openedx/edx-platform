"""
Classes used for defining and running nose test suites
"""
import os
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites.suite import TestSuite
from pavelib.utils.envs import Env

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

__test__ = False  # do not collect


class NoseTestSuite(TestSuite):
    """
    A subclass of TestSuite with extra methods that are specific
    to nose tests
    """
    def __init__(self, *args, **kwargs):
        super(NoseTestSuite, self).__init__(*args, **kwargs)
        self.failed_only = kwargs.get('failed_only', False)
        self.fail_fast = kwargs.get('fail_fast', False)
        self.run_under_coverage = kwargs.get('with_coverage', True)
        self.report_dir = Env.REPORT_DIR / self.root

        # If set, put reports for run in "unique" directories.
        # The main purpose of this is to ensure that the reports can be 'slurped'
        # in the main jenkins flow job without overwriting the reports from other
        # build steps. For local development/testing, this shouldn't be needed.
        if os.environ.get("SHARD", None):
            shard_str = "shard_{}".format(os.environ.get("SHARD"))
            self.report_dir = self.report_dir / shard_str

        self.test_id_dir = Env.TEST_DIR / self.root
        self.test_ids = self.test_id_dir / 'noseids'
        self.extra_args = kwargs.get('extra_args', '')
        self.cov_args = kwargs.get('cov_args', '')
        self.use_ids = True

    def __enter__(self):
        super(NoseTestSuite, self).__enter__()
        self.report_dir.makedirs_p()
        self.test_id_dir.makedirs_p()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Cleans mongo afer the tests run.
        """
        super(NoseTestSuite, self).__exit__(exc_type, exc_value, traceback)
        test_utils.clean_mongo()

    def _under_coverage_cmd(self, cmd):
        """
        If self.run_under_coverage is True, it returns the arg 'cmd'
        altered to be run under coverage. It returns the command
        unaltered otherwise.
        """
        if self.run_under_coverage:
            # We use "python -m coverage" so that the proper python
            # will run the importable coverage rather than the
            # coverage that OS path finds.

            if not cmd[0].endswith('.py'):
                cmd[0] = "`which {}`".format(cmd[0])

            cmd = [
                "python",
                "-m",
                "coverage",
                "run",
                self.cov_args,
                "--rcfile={}".format(Env.PYTHON_COVERAGERC),
            ] + cmd

        return cmd

    @property
    def test_options_flags(self):
        """
        Takes the test options and returns the appropriate flags
        for the command.
        """
        opts = []

        # Handle "--failed" as a special case: we want to re-run only
        # the tests that failed within our Django apps
        # This sets the --failed flag for the nosetests command, so this
        # functionality is the same as described in the nose documentation
        if self.failed_only:
            opts.append("--failed")

        # This makes it so we use nose's fail-fast feature in two cases.
        # Case 1: --fail-fast is passed as an arg in the paver command
        # Case 2: The environment variable TESTS_FAIL_FAST is set as True
        env_fail_fast_set = (
            'TESTS_FAIL_FAST' in os.environ and os.environ['TEST_FAIL_FAST']
        )

        if self.fail_fast or env_fail_fast_set:
            opts.append("--stop")

        if self.use_ids:
            opts.append("--with-id")

        return opts


class SystemTestSuite(NoseTestSuite):
    """
    TestSuite for lms and cms nosetests
    """
    def __init__(self, *args, **kwargs):
        super(SystemTestSuite, self).__init__(*args, **kwargs)
        self.test_id = kwargs.get('test_id', self._default_test_id)
        self.fasttest = kwargs.get('fasttest', False)

        self.processes = kwargs.get('processes', None)
        self.randomize = kwargs.get('randomize', None)

        if self.processes is None:
            # Don't use multiprocessing by default
            self.processes = 0

        self.processes = int(self.processes)

        if self.randomize is None:
            self.randomize = self.root == 'lms'

        if self.processes != 0 and self.verbosity > 1:
            print colorize(
                'red',
                "The TestId module and multiprocessing module can't be run "
                "together in verbose mode. Disabling TestId for {} tests.".format(self.root)
            )
            self.use_ids = False

    def __enter__(self):
        super(SystemTestSuite, self).__enter__()

    @property
    def cmd(self):

        cmd = [
            './manage.py', self.root, 'test',
            '--verbosity={}'.format(self.verbosity),
            self.test_id,
        ] + self.test_options_flags + [
            '--settings=test',
            self.extra_args,
            '--xunitmp-file={}'.format(self.report_dir / "nosetests.xml"),
            '--with-database-isolation',
        ]

        if self.processes != 0:
            cmd.append('--processes={}'.format(self.processes))

        if self.randomize:
            cmd.append('--with-randomly')

        cmd.extend(self.passthrough_options)

        return self._under_coverage_cmd(cmd)

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
        default_test_id = (
            "{system}/djangoapps/*"
            " common/djangoapps/*"
            " openedx/core/djangoapps/*"
            " openedx/tests/*"
            " openedx/core/lib/*"
        )

        if self.root in ('lms', 'cms'):
            default_test_id += " {system}/lib/*"

        if self.root == 'lms':
            default_test_id += " {system}/tests.py"
            default_test_id += " openedx/core/djangolib"

        if self.root == 'cms':
            default_test_id += " {system}/tests/*"

        return default_test_id.format(system=self.root)


class LibTestSuite(NoseTestSuite):
    """
    TestSuite for edx-platform/common/lib nosetests
    """
    def __init__(self, *args, **kwargs):
        super(LibTestSuite, self).__init__(*args, **kwargs)
        self.test_id = kwargs.get('test_id', self.root)
        self.xunit_report = self.report_dir / "nosetests.xml"

    @property
    def cmd(self):
        cmd = [
            "nosetests",
            "--id-file={}".format(self.test_ids),
            self.test_id,
        ] + self.test_options_flags + [
            "--xunit-file={}".format(self.xunit_report),
            self.extra_args,
            "--verbosity={}".format(self.verbosity),
        ] + self.passthrough_options

        return self._under_coverage_cmd(cmd)

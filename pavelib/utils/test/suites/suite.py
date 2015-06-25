"""
A class used for defining and running test suites
"""
import sys
import subprocess
from paver.easy import sh

from pavelib.utils.process import kill_process

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text  # pylint: disable-msg=invalid-name

__test__ = False  # do not collect


class TestSuite(object):
    """
    TestSuite is a class that defines how groups of tests run.
    """
    def __init__(self, *args, **kwargs):
        self.root = args[0]
        self.subsuites = kwargs.get('subsuites', [])
        self.failed_suites = []
        self.verbosity = kwargs.get('verbosity', 1)
        self.skip_clean = kwargs.get('skip_clean', False)
        self.pdb = kwargs.get('pdb', False)

    def __enter__(self):
        """
        This will run before the test suite is run with the run_suite_tests method.
        If self.run_test is called directly, it should be run in a 'with' block to
        ensure that the proper context is created.

        Specific setup tasks should be defined in each subsuite.

        i.e. Checking for and defining required directories.
        """
        print("\nSetting up for {suite_name}".format(suite_name=self.root))
        self.failed_suites = []

    def __exit__(self, exc_type, exc_value, traceback):
        """
        This is run after the tests run with the run_suite_tests method finish.
        Specific clean up tasks should be defined in each subsuite.

        If self.run_test is called directly, it should be run in a 'with' block
        to ensure that clean up happens properly.

        i.e. Cleaning mongo after the lms tests run.
        """
        print("\nCleaning up after {suite_name}".format(suite_name=self.root))

    @property
    def cmd(self):
        """
        The command to run tests (as a string). For this base class there is none.
        """
        return None

    def generate_optimized_static_assets(self):
        """
        Collect static assets using test_static_optimized.py which generates
        optimized files to a dedicated test static root.
        """
        print colorize('green', "Generating optimized static assets...")
        sh("paver update_assets --settings=test_static_optimized")

    def run_test(self):
        """
        Runs a self.cmd in a subprocess and waits for it to finish.
        It returns False if errors or failures occur. Otherwise, it
        returns True.
        """
        cmd = self.cmd
        sys.stdout.write(cmd)

        msg = colorize(
            'green',
            '\n{bar}\n Running tests for {suite_name} \n{bar}\n'.format(suite_name=self.root, bar='=' * 40),
        )

        sys.stdout.write(msg)
        sys.stdout.flush()

        kwargs = {'shell': True, 'cwd': None}
        process = None

        try:
            process = subprocess.Popen(cmd, **kwargs)
            process.communicate()
        except KeyboardInterrupt:
            kill_process(process)
            sys.exit(1)
        else:
            return (process.returncode == 0)

    def run_suite_tests(self):
        """
        Runs each of the suites in self.subsuites while tracking failures
        """
        # Uses __enter__ and __exit__ for context
        with self:
            # run the tests for this class, and for all subsuites
            if self.cmd:
                passed = self.run_test()
                if not passed:
                    self.failed_suites.append(self)

            for suite in self.subsuites:
                suite.run_suite_tests()
                if len(suite.failed_suites) > 0:
                    self.failed_suites.extend(suite.failed_suites)

    def report_test_results(self):
        """
        Writes a list of failed_suites to sys.stderr
        """
        if len(self.failed_suites) > 0:
            msg = colorize('red', "\n\n{bar}\nTests failed in the following suites:\n* ".format(bar="=" * 48))
            msg += colorize('red', '\n* '.join([s.root for s in self.failed_suites]) + '\n\n')
        else:
            msg = colorize('green', "\n\n{bar}\nNo test failures ".format(bar="=" * 48))

        print(msg)

    def run(self):
        """
        Runs the tests in the suite while tracking and reporting failures.
        """
        self.run_suite_tests()
        self.report_test_results()

        if len(self.failed_suites) > 0:
            sys.exit(1)

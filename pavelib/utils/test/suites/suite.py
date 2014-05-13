"""
A class used for defining and running test suites
"""
import sys
import subprocess
from paver.easy import call_task
from pavelib.utils.process import kill_process
from pavelib.utils.test import utils as test_utils

__test__ = False  # do not collect


class TestSuite(object):
    """
    TestSuite is a class that defines how groups of tests run.
    """
    def __init__(self, *args, **kwargs):
        self.root = args[0]
        self.subsuites = kwargs.get('subsuites', [])
        self.run_under_coverage = kwargs.get('with_coverage', False)

        # Initialize vars for tracking failures
        self.failed_suites = []
        self.failed = False

    @property
    def cmd(self):
        """
        The command to run tests (as a string). For this base class there is none.
        """
        return None

    @property
    def under_coverage_cmd(self):
        """
        Returns the given command (str), reformatted to be run with coverage.
        """
        return None

    def _clean_up(self):
        """
        This is run after the tests in this suite finish. Specific
        clean up tasks should be defined in each subsuite.

        i.e. Cleaning mongo after a the lms tests run.
        """
        pass

    def _set_up(self):
        """
        This will run before the test suite is run. Specific setup
        tasks should be defined in each subsuite.

        i.e. Checking for and defining required directories.
        """
        pass

    def run_test(self):
        """
        Runs a test command in a subprocess and waits for it to finish.
        It records the outcome in the self.failed variable.
        """
        msg = test_utils.colorize(
            '\n{bar}\n Running tests for {suite_name} \n{bar}\n'.format(suite_name=self.root, bar='=' * 40),
            'GREEN'
        )

        sys.stdout.write(msg)
        sys.stdout.flush()

        kwargs = {'shell': True, 'cwd': None}
        process = None

        if self.run_under_coverage and self.under_coverage_cmd:
            cmd = self.under_coverage_cmd
        else:
            cmd = self.cmd

        print cmd

        try:
            process = subprocess.Popen(cmd, **kwargs)
            process.communicate()
        except KeyboardInterrupt:
            kill_process(process)
            sys.stderr.write("\nCleaning up before exiting...\n")
            self._clean_up()
            sys.exit(1)
        else:
            self.failed = (process.returncode != 0)

    def run_suite_tests(self):
        """
        Runs each of the specified suites while tracking failures
        """
        # set up
        sys.stdout.write("Setting up for {suite_name}\n".format(suite_name=self.root))
        self._set_up()
        self.failed_suites = []

        # run the tests for this class, and for all subsuites
        if self.cmd:
            self.run_test()
            if self.failed:
                self.failed_suites.append(self)

        for suite in self.subsuites:
            suite.run_suite_tests()
            if suite.failed:
                self.failed = True
                self.failed_suites.extend(suite.failed_suites)

        # clean up
        sys.stdout.write("Cleaning up after {suite_name}\n".format(suite_name=self.root))
        self._clean_up()

    def report_test_failures(self):
        """
        Runs each of the specified suites while tracking and reporting failures
        """
        if self.failed:
            msg = test_utils.colorize("\n\n{bar}\nTests failed in the following suites:\n* ".format(bar="=" * 48), 'RED')
            msg += test_utils.colorize('\n* '.join([s.root for s in self.failed_suites]) + '\n\n', 'RED')
        else:
            msg = test_utils.colorize("\n\n{bar}\nNo test failures\n ".format(bar="=" * 48), 'GREEN')

        sys.stderr.write(msg)

    def run(self, with_build_docs=False):
        """
        Runs the tests in the suite while tracking and reporting failures.
        Optionally, it will also build docs.
        """
        self.run_suite_tests()

        if with_build_docs:
            call_task('pavelib.docs.build_docs')

        self.report_test_failures()

        if self.failed:
            sys.exit(1)

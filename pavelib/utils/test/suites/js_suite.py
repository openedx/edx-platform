"""
Javascript test tasks
"""
from pavelib import assets
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites import TestSuite
from pavelib.utils.envs import Env
import os

__test__ = False  # do not collect


class JsTestSuite(TestSuite):
    """
    A class for running JavaScript tests.
    """
    def __init__(self, *args, **kwargs):
        super(JsTestSuite, self).__init__(*args, **kwargs)
        self.mode = kwargs.get('mode', 'run')

        try:
            self.test_id = (Env.JS_TEST_ID_FILES[Env.JS_TEST_ID_KEYS.index(self.root)])
        except ValueError:
            self.test_id = ' '.join(Env.JS_TEST_ID_FILES)
        except:
            raise

        self.root = self.root + ' javascript'
        self.report_dir, self.coverage_report, self.xunit_report = self._required_dirs()

    @property
    def cmd(self):
        """
        Run the tests using js-test-tool
        See js-test-tool docs for description of different command line arguments
        """
        cmd = "js-test-tool {mode} {test_id} --use-firefox --timeout-sec 600 --xunit-report {xunit_report}".format(
            mode=self.mode, test_id=self.test_id, xunit_report=self.xunit_report)

        return cmd

    @property
    def under_coverage_cmd(self):
        cmd = self.cmd
        if self.run_under_coverage:
            cmd += " --coverage-xml {report_dir}".format(report_dir=self.coverage_report)
        return cmd

    def _set_up(self):
        test_utils.clean_test_files()

        if self.mode == 'run' and not self.run_under_coverage:
            test_utils.clean_dir(self.report_dir)

        assets.compile_coffeescript("`find lms cms common -type f -name \"*.coffee\"`")

    def _required_dirs(self):
        """
        Makes sure that the reports directory is present. Returns paths of report directories and files.
        """
        report_dir = test_utils.get_or_make_dir(Env.JS_REPORT_DIR)
        coverage_report = os.path.join(report_dir, 'coverage.xml')
        xunit_report = os.path.join(report_dir, 'javascript_xunit.xml')

        return report_dir, coverage_report, xunit_report

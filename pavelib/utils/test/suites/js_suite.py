"""
Javascript test tasks
"""
from pavelib import assets
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites.suite import TestSuite
from pavelib.utils.envs import Env

__test__ = False  # do not collect


class JsTestSuite(TestSuite):
    """
    A class for running JavaScript tests.
    """
    def __init__(self, *args, **kwargs):
        super(JsTestSuite, self).__init__(*args, **kwargs)
        self.run_under_coverage = kwargs.get('with_coverage', True)
        self.mode = kwargs.get('mode', 'run')
        self.port = kwargs.get('port')

        try:
            self.test_id = (Env.JS_TEST_ID_FILES[Env.JS_TEST_ID_KEYS.index(self.root)])
        except ValueError:
            self.test_id = ' '.join(Env.JS_TEST_ID_FILES)

        self.root = self.root + ' javascript'
        self.report_dir = Env.JS_REPORT_DIR
        self.coverage_report = self.report_dir / 'coverage.xml'
        self.xunit_report = self.report_dir / 'javascript_xunit.xml'

    def __enter__(self):
        super(JsTestSuite, self).__enter__()
        self.report_dir.makedirs_p()
        if not self.skip_clean:
            test_utils.clean_test_files()

        if self.mode == 'run' and not self.run_under_coverage:
            test_utils.clean_dir(self.report_dir)

        assets.compile_coffeescript("`find lms cms common -type f -name \"*.coffee\"`")

    @property
    def cmd(self):
        """
        Run the tests using js-test-tool. See js-test-tool docs for
        description of different command line arguments.
        """
        cmd = (
            "js-test-tool {mode} {test_id} --use-firefox --timeout-sec "
            "600 --xunit-report {xunit_report}".format(
                mode=self.mode,
                test_id=self.test_id,
                xunit_report=self.xunit_report,
            )
        )

        if self.port:
            cmd += " -p {port}".format(port=self.port)

        if self.run_under_coverage:
            cmd += " --coverage-xml {report_dir}".format(
                report_dir=self.coverage_report
            )

        return cmd

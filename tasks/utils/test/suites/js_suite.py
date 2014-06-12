"""
Javascript test tasks
"""
from tasks import assets
from tasks.utils.test import utils as test_utils
from tasks.utils.test.suites import TestSuite
from tasks.utils.envs import Env

__test__ = False  # do not collect


JS_TEST_IDS = {
    'lms': Env.REPO_ROOT / 'lms/static/js_test.yml',
    'cms': Env.REPO_ROOT / 'cms/static/js_test.yml',
    'cms-squire': Env.REPO_ROOT / 'cms/static/js_test_squire.yml',
    'xmodule': Env.REPO_ROOT / 'common/lib/xmodule/xmodule/js/js_test.yml',
    'common': Env.REPO_ROOT / 'common/static/js_test.yml',
}


class JsTestSuite(TestSuite):
    """
    A class for running JavaScript tests.
    """
    def __init__(self, *args, **kwargs):
        super(JsTestSuite, self).__init__(*args, **kwargs)
        self.run_under_coverage = kwargs.get('with_coverage', True)
        self.mode = kwargs.get('mode', 'run')

        try:
            self.test_id = JS_TEST_IDS[self.root]
        except (KeyError, ValueError):
            self.test_id = " ".join(JS_TEST_IDS.values())

        self.root = self.root + ' javascript'
        self.report_dir = Env.REPORT_DIR / 'javascript'
        self.coverage_report = self.report_dir / 'coverage.xml'
        self.xunit_report = self.report_dir / 'javascript_xunit.xml'

    def __enter__(self):
        super(JsTestSuite, self).__enter__()
        self.report_dir.makedirs_p()
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

        if self.run_under_coverage:
            cmd += " --coverage-xml {report_dir}".format(
                report_dir=self.coverage_report
            )

        return cmd

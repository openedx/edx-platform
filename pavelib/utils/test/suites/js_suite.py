"""
Javascript test tasks
"""

from paver import tasks

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
        suite = args[0]

        try:
            self.test_id = (Env.JS_TEST_CONFIG_FILES[Env.JS_TEST_ID_KEYS.index(self.root)])
        except ValueError:
            self.test_id = ' '.join(Env.JS_TEST_CONFIG_FILES)

        self.root = self.root + ' javascript'
        self.report_dir = Env.JS_REPORT_DIR
        self.coverage_report = self.report_dir / 'coverage-{suite}.xml'.format(suite=suite)
        self.xunit_report = self.report_dir / 'javascript_xunit-{suite}.xml'.format(suite=suite)

    def __enter__(self):
        super(JsTestSuite, self).__enter__()
        if tasks.environment.dry_run:
            tasks.environment.info("make report_dir")
        else:
            self.report_dir.makedirs_p()
        if not self.skip_clean:
            test_utils.clean_test_files()

        if self.mode == 'run' and not self.run_under_coverage:
            test_utils.clean_dir(self.report_dir)

        assets.process_npm_assets()
        assets.compile_coffeescript("`find lms cms common -type f -name \"*.coffee\"`")

    @property
    def cmd(self):
        """
        Run the tests using karma runner.
        """
        cmd = (
            "karma start {test_id} --single-run={single_run} --capture-timeout=60000 "
            "--junitreportpath={xunit_report}".format(
                single_run='false' if self.mode == 'dev' else 'true',
                test_id=self.test_id,
                xunit_report=self.xunit_report,
            )
        )

        if self.mode == 'dev':
            cmd += " --browsers=Chrome"

        if self.port:
            cmd += " --port {port}".format(port=self.port)

        if self.run_under_coverage:
            cmd += " --coverage  --coveragereportpath={report_path}".format(
                report_path=self.coverage_report
            )

        return cmd

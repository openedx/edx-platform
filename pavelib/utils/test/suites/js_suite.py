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
        self.report_dir = Env.JS_REPORT_DIR
        self.opts = kwargs

        suite = args[0]
        self.subsuites = self._default_subsuites if suite == 'all' else [JsTestSubSuite(*args, **kwargs)]

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
    def _default_subsuites(self):
        """
        Returns all JS test suites
        """
        return [JsTestSubSuite(test_id, **self.opts) for test_id in Env.JS_TEST_ID_KEYS]


class JsTestSubSuite(TestSuite):
    """
    Class for JS suites like cms, cms-squire, lms, lms-coffee, common,
    common-requirejs and xmodule
    """
    def __init__(self, *args, **kwargs):
        super(JsTestSubSuite, self).__init__(*args, **kwargs)
        self.test_id = args[0]
        self.run_under_coverage = kwargs.get('with_coverage', True)
        self.mode = kwargs.get('mode', 'run')
        self.port = kwargs.get('port')
        self.root = self.root + ' javascript'
        self.report_dir = Env.JS_REPORT_DIR

        try:
            self.test_conf_file = Env.KARMA_CONFIG_FILES[Env.JS_TEST_ID_KEYS.index(self.test_id)]
        except ValueError:
            self.test_conf_file = Env.KARMA_CONFIG_FILES[0]

        self.coverage_report = self.report_dir / 'coverage-{suite}.xml'.format(suite=self.test_id)
        self.xunit_report = self.report_dir / 'javascript_xunit-{suite}.xml'.format(suite=self.test_id)

    @property
    def cmd(self):
        """
        Run the tests using karma runner.
        """
        cmd = [
            "karma",
            "start",
            self.test_conf_file,
            "--single-run={}".format('false' if self.mode == 'dev' else 'true'),
            "--capture-timeout=60000",
            "--junitreportpath={}".format(self.xunit_report),
        ]

        if self.port:
            cmd.append("--port={}".format(self.port))

        if self.run_under_coverage:
            cmd.extend([
                "--coverage",
                "--coveragereportpath={}".format(self.coverage_report),
            ])

        return cmd

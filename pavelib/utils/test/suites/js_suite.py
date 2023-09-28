"""
Javascript test tasks
"""


from paver import tasks

from pavelib import assets
from pavelib.utils.envs import Env
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites.suite import TestSuite

__test__ = False  # do not collect


class JsTestSuite(TestSuite):
    """
    A class for running JavaScript tests.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_under_coverage = kwargs.get('with_coverage', True)
        self.mode = kwargs.get('mode', 'run')
        self.report_dir = Env.JS_REPORT_DIR
        self.opts = kwargs

        suite = args[0]
        self.subsuites = self._default_subsuites if suite == 'all' else [JsTestSubSuite(*args, **kwargs)]

    def __enter__(self):
        super().__enter__()
        if tasks.environment.dry_run:
            tasks.environment.info("make report_dir")
        else:
            self.report_dir.makedirs_p()
        if not self.skip_clean:
            test_utils.clean_test_files()

        if self.mode == 'run' and not self.run_under_coverage:
            test_utils.clean_dir(self.report_dir)

    @property
    def _default_subsuites(self):
        """
        Returns all JS test suites
        """
        return [JsTestSubSuite(test_id, **self.opts) for test_id in Env.JS_TEST_ID_KEYS if test_id != 'jest-snapshot']


class JsTestSubSuite(TestSuite):
    """
    Class for JS suites like cms, cms-squire, lms, common,
    common-requirejs and xmodule
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

        self.coverage_report = self.report_dir / f'coverage-{self.test_id}.xml'
        self.xunit_report = self.report_dir / f'javascript_xunit-{self.test_id}.xml'

    @property
    def cmd(self):
        """
        Run the tests using karma runner.
        """
        cmd = [
            "node",
            "--max_old_space_size=4096",
            "node_modules/.bin/karma",
            "start",
            self.test_conf_file,
            "--single-run={}".format('false' if self.mode == 'dev' else 'true'),
            "--capture-timeout=60000",
            f"--junitreportpath={self.xunit_report}",
            f"--browsers={Env.KARMA_BROWSER}",
        ]

        if self.port:
            cmd.append(f"--port={self.port}")

        if self.run_under_coverage:
            cmd.extend([
                "--coverage",
                f"--coveragereportpath={self.coverage_report}",
            ])

        return cmd


class JestSnapshotTestSuite(TestSuite):
    """
    A class for running Jest Snapshot tests.
    """
    @property
    def cmd(self):
        """
        Run the tests using Jest.
        """
        return ["jest"]

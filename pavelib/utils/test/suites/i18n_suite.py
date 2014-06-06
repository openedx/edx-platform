"""
Classes used for defining and running i18n test suites
"""
from pavelib.utils.test.suites import TestSuite
from pavelib.utils.envs import Env

__test__ = False  # do not collect


class I18nTestSuite(TestSuite):
    """
    Run tests for the internationalization library
    """
    def __init__(self, *args, **kwargs):
        super(I18nTestSuite, self).__init__(*args, **kwargs)
        self.report_dir = Env.I18N_REPORT_DIR
        self.xunit_report = self.report_dir / 'nosetests.xml'

    def __enter__(self):
        super(I18nTestSuite, self).__enter__()
        self.report_dir.makedirs_p()

    @property
    def cmd(self):
        pythonpath_prefix = (
            "PYTHONPATH={repo_root}/i18n:$PYTHONPATH".format(
                repo_root=Env.REPO_ROOT
            )
        )

        cmd = (
            "{pythonpath_prefix} nosetests {repo_root}/i18n/tests "
            "--with-xunit --xunit-file={xunit_report}".format(
                pythonpath_prefix=pythonpath_prefix,
                repo_root=Env.REPO_ROOT,
                xunit_report=self.xunit_report,
            )
        )

        return cmd

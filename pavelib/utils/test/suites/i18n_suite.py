"""
Classes used for defining and running i18n test suites
"""
import os
from pavelib.utils.test.suites import TestSuite
from pavelib.utils.envs import Env
from pavelib.utils.test import utils as test_utils

__test__ = False  # do not collect


class I18nTestSuite(TestSuite):
    """
    Run tests for the internationalization library
    """
    def __init__(self, *args, **kwargs):
        super(I18nTestSuite, self).__init__(*args, **kwargs)
        self.report_dir, self.xunit_report = self._required_dirs

    def __enter__(self):
        super(I18nTestSuite, self).__enter__()
        test_utils.get_or_make_dir(self.report_dir)

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

    @property
    def _required_dirs(self):
        """
        Makes sure that the reports directory is present.
        Returns paths of report directories and files.
        """
        report_dir = Env.I18N_REPORT_DIR
        xunit_report = os.path.join(report_dir, 'nosetests.xml')

        return report_dir, xunit_report

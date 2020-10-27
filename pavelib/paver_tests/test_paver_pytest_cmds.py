"""
Tests for the pytest paver commands themselves.
Run just this test with: paver test_lib -t pavelib/paver_tests/test_paver_pytest_cmds.py
"""
import unittest
import os
import ddt

from pavelib.utils.test.suites import SystemTestSuite, LibTestSuite
from pavelib.utils.envs import Env


XDIST_TESTING_IP_ADDRESS_LIST = '0.0.0.1,0.0.0.2,0.0.0.3'


@ddt.ddt
class TestPaverPytestCmd(unittest.TestCase):
    """
    Test Paver pytest commands
    """

    def _expected_command(self, root, test_id, pytestSubclass, run_under_coverage=True,
                          processes=0, xdist_ip_addresses=None):
        """
        Returns the command that is expected to be run for the given test spec
        and store.
        """
        report_dir = Env.REPORT_DIR / root
        shard = os.environ.get('SHARD')
        if shard:
            report_dir = report_dir / 'shard_' + shard

        expected_statement = [
            "python",
            "-Wd",
            "-m",
            "pytest"
        ]
        if pytestSubclass == "SystemTestSuite":
            expected_statement.append("--ds={}".format('{}.envs.{}'.format(root, Env.TEST_SETTINGS)))
        expected_statement.append("--junitxml={}".format(report_dir / "nosetests.xml"))

        if xdist_ip_addresses:
            expected_statement.append('--dist=loadscope')
            for ip in xdist_ip_addresses.split(','):
                if processes <= 0:
                    processes = 1

                if pytestSubclass == "SystemTestSuite":
                    django_env_var_cmd = "export DJANGO_SETTINGS_MODULE={}.envs.test".format(root)
                elif pytestSubclass == "LibTestSuite":
                    if 'pavelib/paver_tests' in test_id:
                        django_env_var_cmd = "export DJANGO_SETTINGS_MODULE={}.envs.test".format(root)
                    else:
                        django_env_var_cmd = "export DJANGO_SETTINGS_MODULE='openedx.tests.settings'"

                xdist_string = '--tx {}*ssh="ubuntu@{} -o StrictHostKeyChecking=no"' \
                               '//python="source /edx/app/edxapp/edxapp_env; {}; python"' \
                               '//chdir="/edx/app/edxapp/edx-platform"' \
                               .format(processes, ip, django_env_var_cmd)
                expected_statement.append(xdist_string)
            for rsync_dir in Env.rsync_dirs():
                expected_statement.append('--rsyncdir {}'.format(rsync_dir))
        else:
            if processes == -1:
                expected_statement.append('-n auto')
                expected_statement.append('--dist=loadscope')
            elif processes != 0:
                expected_statement.append('-n {}'.format(processes))
                expected_statement.append('--dist=loadscope')

        expected_statement.extend([
            "-p no:randomly",
            test_id
        ])

        if run_under_coverage:
            expected_statement.append('--cov')
            expected_statement.append('--cov-report=')
        return expected_statement

    @ddt.data('lms', 'cms')
    def test_SystemTestSuite_suites(self, system):
        test_id = 'tests'
        suite = SystemTestSuite(system, test_id=test_id)
        assert suite.cmd == self._expected_command(system, test_id, "SystemTestSuite")

    @ddt.data('lms', 'cms')
    def test_SystemTestSuite_auto_processes(self, system):
        test_id = 'tests'
        suite = SystemTestSuite(system, test_id=test_id, processes=-1)
        assert suite.cmd == self._expected_command(system, test_id, "SystemTestSuite", processes=-1)

    @ddt.data('lms', 'cms')
    def test_SystemTestSuite_multi_processes(self, system):
        test_id = 'tests'
        suite = SystemTestSuite(system, test_id=test_id, processes=3)
        assert suite.cmd == self._expected_command(system, test_id, "SystemTestSuite", processes=3)

    @ddt.data('lms', 'cms')
    def test_SystemTestSuite_with_xdist(self, system):
        test_id = 'tests'
        suite = SystemTestSuite(system, test_id=test_id, xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)
        assert suite.cmd == self._expected_command(system, test_id, "SystemTestSuite",
                                                   xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)

    @ddt.data('lms', 'cms')
    def test_SystemTestSuite_with_xdist_multi_processes(self, system):
        test_id = 'tests'
        suite = SystemTestSuite(system, test_id=test_id, processes=2, xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)
        assert suite.cmd == self._expected_command(system, test_id, "SystemTestSuite", processes=2,
                                                   xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)

    @ddt.data('lms', 'cms')
    def test_SystemTestSuite_with_xdist_negative_processes(self, system):
        test_id = 'tests'
        suite = SystemTestSuite(system, test_id=test_id, processes=-1, xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)
        assert suite.cmd == self._expected_command(system, test_id, "SystemTestSuite", processes=-1,
                                                   xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)

    @ddt.data('common/lib/xmodule', 'pavelib/paver_tests')
    def test_LibTestSuite_suites(self, system):
        test_id = 'tests'
        suite = LibTestSuite(system, test_id=test_id)
        assert suite.cmd == self._expected_command(system, test_id, "LibTestSuite")

    @ddt.data('common/lib/xmodule', 'pavelib/paver_tests')
    def test_LibTestSuite_auto_processes(self, system):
        test_id = 'tests'
        suite = LibTestSuite(system, test_id=test_id, processes=-1)
        assert suite.cmd == self._expected_command(system, test_id, "LibTestSuite", processes=-1)

    @ddt.data('common/lib/xmodule', 'pavelib/paver_tests')
    def test_LibTestSuite_multi_processes(self, system):
        test_id = 'tests'
        suite = LibTestSuite(system, test_id=test_id, processes=3)
        assert suite.cmd == self._expected_command(system, test_id, "LibTestSuite", processes=3)

    @ddt.data('common/lib/xmodule', 'pavelib/paver_tests')
    def test_LibTestSuite_with_xdist(self, system):
        test_id = 'tests'
        suite = LibTestSuite(system, test_id=test_id, xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)
        assert suite.cmd == self._expected_command(system, test_id, "LibTestSuite",
                                                   xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)

    @ddt.data('common/lib/xmodule', 'pavelib/paver_tests')
    def test_LibTestSuite_with_xdist_multi_processes(self, system):
        test_id = 'tests'
        suite = LibTestSuite(system, test_id=test_id, processes=2, xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)
        assert suite.cmd == self._expected_command(system, test_id, "LibTestSuite", processes=2,
                                                   xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)

    @ddt.data('common/lib/xmodule', 'pavelib/paver_tests')
    def test_LibTestSuite_with_xdist_negative_processes(self, system):
        test_id = 'tests'
        suite = LibTestSuite(system, test_id=test_id, processes=-1, xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)
        assert suite.cmd == self._expected_command(system, test_id, "LibTestSuite", processes=-1,
                                                   xdist_ip_addresses=XDIST_TESTING_IP_ADDRESS_LIST)

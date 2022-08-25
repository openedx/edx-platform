"""
Classes used for defining and running pytest test suites
"""


import os
from glob import glob

from pavelib.utils.envs import Env
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites.suite import TestSuite
from pavelib.utils.test.utils import COVERAGE_CACHE_BASELINE, COVERAGE_CACHE_BASEPATH, WHO_TESTS_WHAT_DIFF

__test__ = False  # do not collect


class PytestSuite(TestSuite):
    """
    A subclass of TestSuite with extra methods that are specific
    to pytest tests
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_only = kwargs.get('failed_only', False)
        self.fail_fast = kwargs.get('fail_fast', False)
        self.run_under_coverage = kwargs.get('with_coverage', True)
        django_version = kwargs.get('django_version', None)
        if django_version is None:
            self.django_toxenv = None
        else:
            self.django_toxenv = 'py27-django{}'.format(django_version.replace('.', ''))
        self.disable_courseenrollment_history = kwargs.get('disable_courseenrollment_history', '1')
        self.disable_capture = kwargs.get('disable_capture', None)
        self.report_dir = Env.REPORT_DIR / self.root

        # If set, put reports for run in "unique" directories.
        # The main purpose of this is to ensure that the reports can be 'slurped'
        # in the main jenkins flow job without overwriting the reports from other
        # build steps. For local development/testing, this shouldn't be needed.
        if os.environ.get("SHARD", None):
            shard_str = "shard_{}".format(os.environ.get("SHARD"))
            self.report_dir = self.report_dir / shard_str

        if self.disable_courseenrollment_history:
            os.environ['DISABLE_COURSEENROLLMENT_HISTORY'] = '1'

        self.xunit_report = self.report_dir / "nosetests.xml"

        self.cov_args = kwargs.get('cov_args', '')
        self.with_wtw = kwargs.get('with_wtw', False)

    def __enter__(self):
        super().__enter__()
        self.report_dir.makedirs_p()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Cleans mongo afer the tests run.
        """
        super().__exit__(exc_type, exc_value, traceback)
        test_utils.clean_mongo()

    def _under_coverage_cmd(self, cmd):
        """
        If self.run_under_coverage is True, it returns the arg 'cmd'
        altered to be run under coverage. It returns the command
        unaltered otherwise.
        """
        if self.run_under_coverage:
            cmd.append('--cov')
            cmd.append('--cov-report=')

        return cmd

    @staticmethod
    def is_success(exit_code):
        """
        An exit code of zero means all tests passed, 5 means no tests were
        found.
        """
        return exit_code in [0, 5]

    @property
    def test_options_flags(self):
        """
        Takes the test options and returns the appropriate flags
        for the command.
        """
        opts = []

        # Handle "--failed" as a special case: we want to re-run only
        # the tests that failed within our Django apps
        # This sets the --last-failed flag for the pytest command, so this
        # functionality is the same as described in the pytest documentation
        if self.failed_only:
            opts.append("--last-failed")

        # This makes it so we use pytest's fail-fast feature in two cases.
        # Case 1: --fail-fast is passed as an arg in the paver command
        # Case 2: The environment variable TESTS_FAIL_FAST is set as True
        env_fail_fast_set = (
            'TESTS_FAIL_FAST' in os.environ and os.environ['TEST_FAIL_FAST']
        )

        if self.fail_fast or env_fail_fast_set:
            opts.append("--exitfirst")

        if self.with_wtw:
            opts.extend([
                '--wtw',
                f'{COVERAGE_CACHE_BASEPATH}/{WHO_TESTS_WHAT_DIFF}',
                '--wtwdb',
                f'{COVERAGE_CACHE_BASEPATH}/{COVERAGE_CACHE_BASELINE}'
            ])

        return opts


class SystemTestSuite(PytestSuite):
    """
    TestSuite for lms and cms python unit tests
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eval_attr = kwargs.get('eval_attr', None)
        self.test_id = kwargs.get('test_id', self._default_test_id)
        self.fasttest = kwargs.get('fasttest', False)
        self.disable_migrations = kwargs.get('disable_migrations', True)
        self.processes = kwargs.get('processes', None)
        self.randomize = kwargs.get('randomize', None)
        self.settings = kwargs.get('settings', Env.TEST_SETTINGS)
        self.xdist_ip_addresses = kwargs.get('xdist_ip_addresses', None)

        if self.processes is None:
            # Don't use multiprocessing by default
            self.processes = 0

        self.processes = int(self.processes)

    def _under_coverage_cmd(self, cmd):
        """
        If self.run_under_coverage is True, it returns the arg 'cmd'
        altered to be run under coverage. It returns the command
        unaltered otherwise.
        """
        if self.run_under_coverage:
            cmd.append('--cov')
            cmd.append('--cov-report=')

        return cmd

    @property
    def cmd(self):
        if self.django_toxenv:
            cmd = ['tox', '-e', self.django_toxenv, '--']
        else:
            cmd = []
        cmd.extend([
            'python',
            '-Wd',
            '-m',
            'pytest',
            '--ds={}'.format(f'{self.root}.envs.{self.settings}'),
            f"--junitxml={self.xunit_report}",
        ])
        cmd.extend(self.test_options_flags)
        if self.verbosity < 1:
            cmd.append("--quiet")
        elif self.verbosity > 1:
            # currently only two verbosity settings are supported, so using `-vvv`
            # in place of `--verbose`, because it is needed to see migrations.
            cmd.append("-vvv")

        if self.disable_capture:
            cmd.append("-s")

        if not self.disable_migrations:
            cmd.append("--migrations")

        if self.xdist_ip_addresses:
            cmd.append('--dist=loadscope')
            if self.processes <= 0:
                xdist_remote_processes = 1
            else:
                xdist_remote_processes = self.processes
            for ip in self.xdist_ip_addresses.split(','):
                # Propogate necessary env vars to xdist containers
                env_var_cmd = 'export DJANGO_SETTINGS_MODULE={} DISABLE_COURSEENROLLMENT_HISTORY={} PYTHONHASHSEED=0'\
                    .format(f'{self.root}.envs.{self.settings}',
                            self.disable_courseenrollment_history)
                xdist_string = '--tx {}*ssh="jenkins@{} -o StrictHostKeyChecking=no"' \
                               '//python="source edx-venv-{}/edx-venv/bin/activate; {}; python"' \
                               '//chdir="edx-platform"' \
                               .format(xdist_remote_processes, ip, Env.PYTHON_VERSION, env_var_cmd)
                cmd.append(xdist_string)
            for rsync_dir in Env.rsync_dirs():
                cmd.append(f'--rsyncdir {rsync_dir}')
        else:
            if self.processes == -1:
                cmd.append('-n auto')
                cmd.append('--dist=loadscope')
            elif self.processes != 0:
                cmd.append(f'-n {self.processes}')
                cmd.append('--dist=loadscope')

        if not self.randomize:
            cmd.append('-p no:randomly')
        if self.eval_attr:
            cmd.append(f"-a '{self.eval_attr}'")

        cmd.extend(self.passthrough_options)
        cmd.append(self.test_id)

        return self._under_coverage_cmd(cmd)

    @property
    def _default_test_id(self):
        """
        If no test id is provided, we need to limit the test runner
        to the Djangoapps we want to test.  Otherwise, it will
        run tests on all installed packages. We do this by
        using a default test id.
        """
        # We need to use $DIR/*, rather than just $DIR so that
        # pytest will import them early in the test process,
        # thereby making sure that we load any django models that are
        # only defined in test files.
        default_test_globs = [
            f"{self.root}/djangoapps/*",
            "common/djangoapps/*",
            "openedx/core/djangoapps/*",
            "openedx/tests/*",
            "openedx/core/lib/*",
        ]
        if self.root in ('lms', 'cms'):
            default_test_globs.append(f"{self.root}/lib/*")

        if self.root == 'lms':
            default_test_globs.append(f"{self.root}/tests.py")
            default_test_globs.append("openedx/core/djangolib/*")
            default_test_globs.append("openedx/core/tests/*")
            default_test_globs.append("openedx/features")

        def included(path):
            """
            Should this path be included in the pytest arguments?
            """
            if path.endswith(Env.IGNORED_TEST_DIRS):
                return False
            return path.endswith('.py') or os.path.isdir(path)

        default_test_paths = []
        for path_glob in default_test_globs:
            if '*' in path_glob:
                default_test_paths += [path for path in glob(path_glob) if included(path)]
            else:
                default_test_paths += [path_glob]
        return ' '.join(default_test_paths)


class LibTestSuite(PytestSuite):
    """
    TestSuite for edx-platform/pavelib/paver_tests python unit tests
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.append_coverage = kwargs.get('append_coverage', False)
        self.test_id = kwargs.get('test_id', self.root)
        self.eval_attr = kwargs.get('eval_attr', None)
        self.xdist_ip_addresses = kwargs.get('xdist_ip_addresses', None)
        self.randomize = kwargs.get('randomize', None)
        self.processes = kwargs.get('processes', None)

        if self.processes is None:
            # Don't use multiprocessing by default
            self.processes = 0

        self.processes = int(self.processes)

    @property
    def cmd(self):
        if self.django_toxenv:
            cmd = ['tox', '-e', self.django_toxenv, '--']
        else:
            cmd = []
        cmd.extend([
            'python',
            '-Wd',
            '-m',
            'pytest',
            f'--junitxml={self.xunit_report}',
        ])
        cmd.extend(self.passthrough_options + self.test_options_flags)
        if self.verbosity < 1:
            cmd.append("--quiet")
        elif self.verbosity > 1:
            # currently only two verbosity settings are supported, so using `-vvv`
            # in place of `--verbose`, because it is needed to see migrations.
            cmd.append("-vvv")
        if self.disable_capture:
            cmd.append("-s")

        if self.xdist_ip_addresses:
            cmd.append('--dist=loadscope')
            if self.processes <= 0:
                xdist_remote_processes = 1
            else:
                xdist_remote_processes = self.processes
            for ip in self.xdist_ip_addresses.split(','):
                # Propogate necessary env vars to xdist containers
                django_env_var_cmd = "export DJANGO_SETTINGS_MODULE='lms.envs.test'"

                env_var_cmd = '{} DISABLE_COURSEENROLLMENT_HISTORY={}' \
                    .format(django_env_var_cmd, self.disable_courseenrollment_history)

                xdist_string = '--tx {}*ssh="jenkins@{} -o StrictHostKeyChecking=no"' \
                               '//python="source edx-venv-{}/edx-venv/bin/activate; {}; python"' \
                               '//chdir="edx-platform"' \
                               .format(xdist_remote_processes, ip, Env.PYTHON_VERSION, env_var_cmd)
                cmd.append(xdist_string)
            for rsync_dir in Env.rsync_dirs():
                cmd.append(f'--rsyncdir {rsync_dir}')
            # "--rsyncdir" throws off the configuration root, set it explicitly
            cmd.append('--rootdir=pavelib/paver_tests')
        else:
            if self.processes == -1:
                cmd.append('-n auto')
                cmd.append('--dist=loadscope')
            elif self.processes != 0:
                cmd.append(f'-n {self.processes}')
                cmd.append('--dist=loadscope')

        if not self.randomize:
            cmd.append("-p no:randomly")
        if self.eval_attr:
            cmd.append(f"-a '{self.eval_attr}'")

        cmd.append(self.test_id)

        return self._under_coverage_cmd(cmd)

    def _under_coverage_cmd(self, cmd):
        """
        If self.run_under_coverage is True, it returns the arg 'cmd'
        altered to be run under coverage. It returns the command
        unaltered otherwise.
        """
        if self.run_under_coverage:
            cmd.append('--cov')
            if self.append_coverage:
                cmd.append('--cov-append')
            cmd.append('--cov-report=')

        return cmd

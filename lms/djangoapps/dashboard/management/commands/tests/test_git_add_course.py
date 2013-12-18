"""
Provide tests for git_add_course management command.
"""

import unittest
import os
import shutil
import subprocess

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test.utils import override_settings

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
import dashboard.management.commands.git_add_course as git_add_course

TEST_MONGODB_LOG = {
    'host': 'localhost',
    'user': '',
    'password': '',
    'db': 'test_xlog',
}

FEATURES_WITH_SSL_AUTH = settings.FEATURES.copy()
FEATURES_WITH_SSL_AUTH['AUTH_USE_MIT_CERTIFICATES'] = True


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
@override_settings(MONGODB_LOG=TEST_MONGODB_LOG)
@unittest.skipUnless(settings.FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'),
                     "ENABLE_SYSADMIN_DASHBOARD not set")
class TestGitAddCourse(ModuleStoreTestCase):
    """
    Tests the git_add_course management command for proper functions.
    """

    TEST_REPO = 'https://github.com/mitocw/edx4edx_lite.git'

    def assertCommandFailureRegexp(self, regex, *args):
        """
        Convenience function for testing command failures
        """
        with self.assertRaises(SystemExit):
            self.assertRaisesRegexp(CommandError, regex,
                                    call_command('git_add_course', *args))

    def test_command_args(self):
        """
        Validate argument checking
        """
        self.assertCommandFailureRegexp(
            'This script requires at least one argument, the git URL')
        self.assertCommandFailureRegexp(
            'This script requires no more than two arguments',
            'blah', 'blah', 'blah')
        self.assertCommandFailureRegexp(
            'Repo was not added, check log output for details',
            'blah')
        # Test successful import from command
        try:
            os.mkdir(getattr(settings, 'GIT_REPO_DIR'))
        except OSError:
            pass

        # Make a course dir that will be replaced with a symlink
        # while we are at it.
        if not os.path.isdir(getattr(settings, 'GIT_REPO_DIR') / 'edx4edx'):
            os.mkdir(getattr(settings, 'GIT_REPO_DIR') / 'edx4edx')

        call_command('git_add_course', self.TEST_REPO,
                     getattr(settings, 'GIT_REPO_DIR') / 'edx4edx_lite')
        if os.path.isdir(getattr(settings, 'GIT_REPO_DIR')):
            shutil.rmtree(getattr(settings, 'GIT_REPO_DIR'))

    def test_add_repo(self):
        """
        Various exit path tests for test_add_repo
        """
        self.assertEqual(git_add_course.GIT_IMPORT_NO_DIR,
                         git_add_course.add_repo(self.TEST_REPO, None))
        try:
            os.mkdir(getattr(settings, 'GIT_REPO_DIR'))
        except OSError:
            pass
        self.assertEqual(git_add_course.GIT_IMPORT_URL_BAD,
                         git_add_course.add_repo('foo', None))

        self.assertEqual(
            git_add_course.GIT_IMPORT_CANNOT_PULL,
            git_add_course.add_repo('file:///foobar.git', None)
        )

        # Test git repo that exists, but is "broken"
        bare_repo = os.path.abspath('{0}/{1}'.format(settings.TEST_ROOT, 'bare.git'))
        os.mkdir(os.path.abspath(bare_repo))
        subprocess.call(['git', '--bare', 'init', ], cwd=bare_repo)

        self.assertEqual(
            git_add_course.GIT_IMPORT_BAD_REPO,
            git_add_course.add_repo('file://{0}'.format(bare_repo), None)
        )
        shutil.rmtree(bare_repo)

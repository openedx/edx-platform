"""
Unittests for exporting to git via management command.
"""

import copy
import os
import shutil
import StringIO
import subprocess
import unittest
from uuid import uuid4

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test.utils import override_settings

from contentstore.tests.utils import CourseTestCase
import contentstore.management.commands.git_export as git_export
from contentstore.management.commands.git_export import GitExportError

FEATURES_WITH_PUSH_TO_LMS = settings.FEATURES.copy()
FEATURES_WITH_PUSH_TO_LMS['ENABLE_PUSH_TO_LMS'] = True
TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
@override_settings(FEATURES=FEATURES_WITH_PUSH_TO_LMS)
class TestGitExport(CourseTestCase):
    """
    Excercise the git_export django management command with various inputs.
    """

    def setUp(self):
        """
        Create/reinitialize bare repo and folders needed
        """
        super(TestGitExport, self).setUp()

        if not os.path.isdir(git_export.GIT_REPO_EXPORT_DIR):
            os.mkdir(git_export.GIT_REPO_EXPORT_DIR)
            self.addCleanup(shutil.rmtree, git_export.GIT_REPO_EXPORT_DIR)

        self.bare_repo_dir = '{0}/data/test_bare.git'.format(
            os.path.abspath(settings.TEST_ROOT))
        if not os.path.isdir(self.bare_repo_dir):
            os.mkdir(self.bare_repo_dir)
            self.addCleanup(shutil.rmtree, self.bare_repo_dir)
        subprocess.check_output(['git', '--bare', 'init', ],
                                cwd=self.bare_repo_dir)

    def test_command(self):
        """
        Test that the command interface works. Ignore stderr fo clean
        test output.
        """
        with self.assertRaises(SystemExit) as ex:
            self.assertRaisesRegexp(
                CommandError, 'This script requires.*',
                call_command('git_export', 'blah', 'blah', 'blah',
                             stderr=StringIO.StringIO()))
        self.assertEqual(ex.exception.code, 1)

        with self.assertRaises(SystemExit) as ex:
            self.assertRaisesRegexp(CommandError, 'This script requires.*',
                                    call_command('git_export',
                                                 stderr=StringIO.StringIO()))
        self.assertEqual(ex.exception.code, 1)

        # Send bad url to get course not exported
        with self.assertRaises(SystemExit) as ex:
            self.assertRaisesRegexp(CommandError, GitExportError.URL_BAD,
                                    call_command('git_export', 'foo', 'silly',
                                                 stderr=StringIO.StringIO()))
        self.assertEqual(ex.exception.code, 1)

    def test_bad_git_url(self):
        """
        Test several bad URLs for validation
        """
        with self.assertRaisesRegexp(GitExportError, GitExportError.URL_BAD):
            git_export.export_to_git('', 'Sillyness')

        with self.assertRaisesRegexp(GitExportError, GitExportError.URL_BAD):
            git_export.export_to_git('', 'example.com:edx/notreal')

        with self.assertRaisesRegexp(GitExportError,
                                     GitExportError.URL_NO_AUTH):
            git_export.export_to_git('', 'http://blah')

    def test_bad_git_repos(self):
        """
        Test invalid git repos
        """
        test_repo_path = '{}/test_repo'.format(git_export.GIT_REPO_EXPORT_DIR)
        self.assertFalse(os.path.isdir(test_repo_path))
        # Test bad clones
        with self.assertRaisesRegexp(GitExportError,
                                     GitExportError.CANNOT_PULL):
            git_export.export_to_git(
                'foo/blah/100',
                'https://user:blah@example.com/test_repo.git')
        self.assertFalse(os.path.isdir(test_repo_path))

        # Setup good repo with bad course to test xml export
        with self.assertRaisesRegexp(GitExportError,
                                     GitExportError.XML_EXPORT_FAIL):
            git_export.export_to_git(
                'foo/blah/100',
                'file://{0}'.format(self.bare_repo_dir))

        # Test bad git remote after successful clone
        with self.assertRaisesRegexp(GitExportError,
                                     GitExportError.CANNOT_PULL):
            git_export.export_to_git(
                'foo/blah/100',
                'https://user:blah@example.com/r.git')

    def test_bad_course_id(self):
        """
        Test valid git url, but bad course.
        """
        with self.assertRaisesRegexp(GitExportError, GitExportError.BAD_COURSE):
            git_export.export_to_git(
                '', 'file://{0}'.format(self.bare_repo_dir), '', '/blah')

    @unittest.skipIf(os.environ.get('GIT_CONFIG') or
                     os.environ.get('GIT_AUTHOR_EMAIL') or
                     os.environ.get('GIT_AUTHOR_NAME') or
                     os.environ.get('GIT_COMMITTER_EMAIL') or
                     os.environ.get('GIT_COMMITTER_NAME'),
                     'Global git override set')
    def test_git_ident(self):
        """
        Test valid course with and without user specified.

        Test skipped if git global config override environment variable GIT_CONFIG
        is set.
        """
        git_export.export_to_git(
            self.course.id,
            'file://{0}'.format(self.bare_repo_dir),
            'enigma'
        )
        expect_string = '{0}|{1}\n'.format(
            git_export.GIT_EXPORT_DEFAULT_IDENT['name'],
            git_export.GIT_EXPORT_DEFAULT_IDENT['email']
        )
        cwd = os.path.abspath(git_export.GIT_REPO_EXPORT_DIR / 'test_bare')
        git_log = subprocess.check_output(['git', 'log', '-1',
                                           '--format=%an|%ae', ], cwd=cwd)
        self.assertEqual(expect_string, git_log)

        # Make changes to course so there is something commit
        self.populateCourse()
        git_export.export_to_git(
            self.course.id,
            'file://{0}'.format(self.bare_repo_dir),
            self.user.username
        )
        expect_string = '{0}|{1}\n'.format(
            self.user.username,
            self.user.email,
        )
        git_log = subprocess.check_output(
            ['git', 'log', '-1', '--format=%an|%ae', ], cwd=cwd)
        self.assertEqual(expect_string, git_log)

    def test_no_change(self):
        """
        Test response if there are no changes
        """
        git_export.export_to_git(
            'i4x://{0}'.format(self.course.id),
            'file://{0}'.format(self.bare_repo_dir)
        )

        with self.assertRaisesRegexp(GitExportError,
                                     GitExportError.CANNOT_COMMIT):
            git_export.export_to_git(
                self.course.id, 'file://{0}'.format(self.bare_repo_dir))

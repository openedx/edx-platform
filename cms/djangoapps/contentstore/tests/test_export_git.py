"""
Test the ability to export courses to xml from studio
"""

import copy
import os
import shutil
import subprocess
from uuid import uuid4

from django.conf import settings
from django.test.utils import override_settings

from .utils import CourseTestCase
import contentstore.git_export_utils as git_export_utils
from xmodule.contentstore.django import _CONTENTSTORE
from xmodule.modulestore.django import modulestore
from contentstore.utils import reverse_course_url

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class TestExportGit(CourseTestCase):
    """
    Tests pushing a course to a git repository
    """

    def setUp(self):
        """
        Setup test course, user, and url.
        """
        super(TestExportGit, self).setUp()
        self.course_module = modulestore().get_course(self.course.id)
        self.test_url = reverse_course_url('export_git', self.course.id)

    def tearDown(self):
        modulestore().contentstore.drop_database()
        _CONTENTSTORE.clear()

    def test_giturl_missing(self):
        """
        Test to make sure an appropriate error is displayed
        if course hasn't set giturl.
        """
        response = self.client.get(self.test_url)
        self.assertEqual(200, response.status_code)
        self.assertIn(
            ('giturl must be defined in your '
             'course settings before you can export to git.'),
            response.content
        )

        response = self.client.get('{}?action=push'.format(self.test_url))
        self.assertEqual(200, response.status_code)
        self.assertIn(
            ('giturl must be defined in your '
             'course settings before you can export to git.'),
            response.content
        )

    def test_course_export_failures(self):
        """
        Test failed course export response.
        """
        self.course_module.giturl = 'foobar'
        modulestore().update_item(self.course_module, '**replace_user**')

        response = self.client.get('{}?action=push'.format(self.test_url))
        self.assertIn('Export Failed:', response.content)

    def test_exception_translation(self):
        """
        Regression test for making sure errors are properly stringified
        """
        self.course_module.giturl = 'foobar'
        modulestore().update_item(self.course_module, '**replace_user**')

        response = self.client.get('{}?action=push'.format(self.test_url))
        self.assertNotIn('django.utils.functional.__proxy__', response.content)

    def test_course_export_success(self):
        """
        Test successful course export response.
        """
        # Build out local bare repo, and set course git url to it
        repo_dir = os.path.abspath(git_export_utils.GIT_REPO_EXPORT_DIR)
        os.mkdir(repo_dir)
        self.addCleanup(shutil.rmtree, repo_dir)

        bare_repo_dir = '{0}/test_repo.git'.format(
            os.path.abspath(git_export_utils.GIT_REPO_EXPORT_DIR))
        os.mkdir(bare_repo_dir)
        self.addCleanup(shutil.rmtree, bare_repo_dir)

        subprocess.check_output(['git', '--bare', 'init', ], cwd=bare_repo_dir)

        self.populate_course()
        self.course_module.giturl = 'file://{}'.format(bare_repo_dir)
        modulestore().update_item(self.course_module, '**replace_user**')

        response = self.client.get('{}?action=push'.format(self.test_url))
        self.assertIn('Export Succeeded', response.content)

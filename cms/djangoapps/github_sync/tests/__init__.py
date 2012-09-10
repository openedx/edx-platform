from django.test import TestCase
from path import path
import shutil
from github_sync import (
    import_from_github, export_to_github, load_repo_settings,
    sync_all_with_github, sync_with_github
)
from git import Repo
from django.conf import settings
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from override_settings import override_settings
from github_sync.exceptions import GithubSyncError
from mock import patch, Mock

REPO_DIR = settings.GITHUB_REPO_ROOT / 'local_repo'
WORKING_DIR = path(settings.TEST_ROOT)
REMOTE_DIR = WORKING_DIR / 'remote_repo'


@override_settings(REPOS={
    'local_repo': {
        'origin': REMOTE_DIR,
        'branch': 'master',
    }
})
class GithubSyncTestCase(TestCase):

    def cleanup(self):
        shutil.rmtree(REPO_DIR, ignore_errors=True)
        shutil.rmtree(REMOTE_DIR, ignore_errors=True)
        modulestore().collection.drop()

    def setUp(self):
        # make sure there's no stale data lying around
        self.cleanup()

        shutil.copytree('common/test/data/toy', REMOTE_DIR)

        remote = Repo.init(REMOTE_DIR)
        remote.git.add(A=True)
        remote.git.commit(m='Initial commit')
        remote.git.config("receive.denyCurrentBranch", "ignore")

        self.import_revision, self.import_course = import_from_github(load_repo_settings('local_repo'))

    def tearDown(self):
        self.cleanup()

    def test_initialize_repo(self):
        """
        Test that importing from github will create a repo if the repo doesn't already exist
        """
        self.assertEquals(1, len(Repo(REPO_DIR).head.reference.log()))

    def test_import_contents(self):
        """
        Test that the import loads the correct course into the modulestore
        """
        self.assertEquals('Toy Course', self.import_course.metadata['display_name'])
        self.assertIn(
            Location('i4x://edX/toy/chapter/Overview'),
            [child.location for child in self.import_course.get_children()])
        self.assertEquals(2, len(self.import_course.get_children()))

    @patch('github_sync.sync_with_github')
    def test_sync_all_with_github(self, sync_with_github):
        sync_all_with_github()
        sync_with_github.assert_called_with(load_repo_settings('local_repo'))

    def test_sync_with_github(self):
        with patch('github_sync.import_from_github', Mock(return_value=(Mock(), Mock()))) as import_from_github:
            with patch('github_sync.export_to_github') as export_to_github:
                settings = load_repo_settings('local_repo')
                sync_with_github(settings)
                import_from_github.assert_called_with(settings)
                export_to_github.assert_called

    @override_settings(MITX_FEATURES={'GITHUB_PUSH': False})
    def test_export_no_pash(self):
        """
        Test that with the GITHUB_PUSH feature disabled, no content is pushed to the remote
        """
        export_to_github(self.import_course, 'Test no-push')
        self.assertEquals(1, Repo(REMOTE_DIR).head.commit.count())

    @override_settings(MITX_FEATURES={'GITHUB_PUSH': True})
    def test_export_push(self):
        """
        Test that with GITHUB_PUSH enabled, content is pushed to the remote
        """
        self.import_course.metadata['display_name'] = 'Changed display name'
        export_to_github(self.import_course, 'Test push')
        self.assertEquals(2, Repo(REMOTE_DIR).head.commit.count())

    @override_settings(MITX_FEATURES={'GITHUB_PUSH': True})
    def test_export_conflict(self):
        """
        Test that if there is a conflict when pushing to the remote repo, nothing is pushed and an exception is raised
        """
        self.import_course.metadata['display_name'] = 'Changed display name'

        remote = Repo(REMOTE_DIR)
        remote.git.commit(allow_empty=True, m="Testing conflict commit")

        self.assertRaises(GithubSyncError, export_to_github, self.import_course, 'Test push')
        self.assertEquals(2, remote.head.reference.commit.count())
        self.assertEquals("Testing conflict commit\n", remote.head.reference.commit.message)

import json
from django.test.client import Client
from django.test import TestCase
from mock import patch, Mock
from override_settings import override_settings
from django.conf import settings


@override_settings(REPOS={'repo': {'path': 'path', 'branch': 'branch'}})
class PostReceiveTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('github_sync.views.export_to_github')
    @patch('github_sync.views.import_from_github')
    def test_non_branch(self, import_from_github, export_to_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/tags/foo'})
        })
        self.assertFalse(import_from_github.called)
        self.assertFalse(export_to_github.called)

    @patch('github_sync.views.export_to_github')
    @patch('github_sync.views.import_from_github')
    def test_non_watched_repo(self, import_from_github, export_to_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/heads/branch',
            'repository': {'name': 'bad_repo'}})
        })
        self.assertFalse(import_from_github.called)
        self.assertFalse(export_to_github.called)

    @patch('github_sync.views.export_to_github')
    @patch('github_sync.views.import_from_github')
    def test_non_tracked_branch(self, import_from_github, export_to_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/heads/non_branch',
            'repository': {'name': 'repo'}})
        })
        self.assertFalse(import_from_github.called)
        self.assertFalse(export_to_github.called)

    @patch('github_sync.views.export_to_github')
    @patch('github_sync.views.import_from_github', return_value=(Mock(), Mock()))
    def test_tracked_branch(self, import_from_github, export_to_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/heads/branch',
            'repository': {'name': 'repo'}})
        })
        import_from_github.assert_called_with(settings.REPOS['repo'])
        mock_revision, mock_course = import_from_github.return_value
        export_to_github.assert_called_with(mock_course, 'path', "Changes from cms import of revision %s" % mock_revision)


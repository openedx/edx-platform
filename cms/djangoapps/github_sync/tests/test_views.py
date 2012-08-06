import json
from django.test.client import Client
from django.test import TestCase
from mock import patch
from override_settings import override_settings
from github_sync import load_repo_settings


@override_settings(REPOS={'repo': {'branch': 'branch', 'origin': 'origin'}})
class PostReceiveTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('github_sync.views.import_from_github')
    def test_non_branch(self, import_from_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/tags/foo'})
        })
        self.assertFalse(import_from_github.called)

    @patch('github_sync.views.import_from_github')
    def test_non_watched_repo(self, import_from_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/heads/branch',
            'repository': {'name': 'bad_repo'}})
        })
        self.assertFalse(import_from_github.called)

    @patch('github_sync.views.import_from_github')
    def test_non_tracked_branch(self, import_from_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/heads/non_branch',
            'repository': {'name': 'repo'}})
        })
        self.assertFalse(import_from_github.called)

    @patch('github_sync.views.import_from_github')
    def test_tracked_branch(self, import_from_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/heads/branch',
            'repository': {'name': 'repo'}})
        })
        import_from_github.assert_called_with(load_repo_settings('repo'))

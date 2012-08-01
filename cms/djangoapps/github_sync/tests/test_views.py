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

    @patch('github_sync.views.sync_with_github')
    def test_non_branch(self, sync_with_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/tags/foo'})
        })
        self.assertFalse(sync_with_github.called)

    @patch('github_sync.views.sync_with_github')
    def test_non_watched_repo(self, sync_with_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/heads/branch',
            'repository': {'name': 'bad_repo'}})
        })
        self.assertFalse(sync_with_github.called)

    @patch('github_sync.views.sync_with_github')
    def test_non_tracked_branch(self, sync_with_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/heads/non_branch',
            'repository': {'name': 'repo'}})
        })
        self.assertFalse(sync_with_github.called)

    @patch('github_sync.views.sync_with_github')
    def test_tracked_branch(self, sync_with_github):
        self.client.post('/github_service_hook', {'payload': json.dumps({
            'ref': 'refs/heads/branch',
            'repository': {'name': 'repo'}})
        })
        sync_with_github.assert_called_with(load_repo_settings('repo'))

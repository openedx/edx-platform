import unittest as unittest

from ...backends.github import GithubOAuth2
from ...backends.utils import get_backend, load_backends
from ...exceptions import MissingBackend
from ..models import TestStorage
from ..strategy import TestStrategy


class BaseBackendUtilsTest(unittest.TestCase):
    def setUp(self):
        self.strategy = TestStrategy(storage=TestStorage)

    def tearDown(self):
        self.strategy = None


class LoadBackendsTest(BaseBackendUtilsTest):
    def test_load_backends(self):
        loaded_backends = load_backends((
            'social_core.backends.github.GithubOAuth2',
            'social_core.backends.facebook.FacebookOAuth2',
            'social_core.backends.flickr.FlickrOAuth'
        ), force_load=True)
        keys = list(loaded_backends.keys())
        self.assertEqual(keys, ['github', 'facebook', 'flickr'])

        backends = ()
        loaded_backends = load_backends(backends, force_load=True)
        self.assertEqual(len(list(loaded_backends.keys())), 0)


class GetBackendTest(BaseBackendUtilsTest):
    def test_get_backend(self):
        backend = get_backend((
            'social_core.backends.github.GithubOAuth2',
            'social_core.backends.facebook.FacebookOAuth2',
            'social_core.backends.flickr.FlickrOAuth'
        ), 'github')
        self.assertEqual(backend, GithubOAuth2)

    def test_get_missing_backend(self):
        with self.assertRaisesRegex(MissingBackend,
                                    'Missing backend "foobar" entry'):
            get_backend(('social_core.backends.github.GithubOAuth2',
                         'social_core.backends.facebook.FacebookOAuth2',
                         'social_core.backends.flickr.FlickrOAuth'),
                        'foobar')

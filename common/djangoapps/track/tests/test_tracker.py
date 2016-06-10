from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

import track.tracker as tracker
from track.backends import BaseBackend


SIMPLE_SETTINGS = {
    'default': {
        'ENGINE': 'track.tests.test_tracker.DummyBackend',
        'OPTIONS': {
            'flag': True
        }
    }
}

MULTI_SETTINGS = {
    'first': {
        'ENGINE': 'track.tests.test_tracker.DummyBackend',
    },
    'second': {
        'ENGINE': 'track.tests.test_tracker.DummyBackend',
    }
}


class TestTrackerInstantiation(TestCase):
    """Test that a helper function can instantiate backends from their name."""
    def setUp(self):
        # pylint: disable=protected-access
        super(TestTrackerInstantiation, self).setUp()
        self.get_backend = tracker._instantiate_backend_from_name

    def test_instatiate_backend(self):
        name = 'track.tests.test_tracker.DummyBackend'
        options = {'flag': True}
        backend = self.get_backend(name, options)

        self.assertIsInstance(backend, DummyBackend)
        self.assertTrue(backend.flag)

    def test_instatiate_backends_with_invalid_values(self):
        def get_invalid_backend(name, parameters):
            return self.get_backend(name, parameters)

        options = {}
        name = 'track.backends.logger'
        self.assertRaises(ValueError, get_invalid_backend, name, options)

        name = 'track.backends.logger.Foo'
        self.assertRaises(ValueError, get_invalid_backend, name, options)

        name = 'this.package.does.not.exists'
        self.assertRaises(ValueError, get_invalid_backend, name, options)

        name = 'unittest.TestCase'
        self.assertRaises(ValueError, get_invalid_backend, name, options)


class TestTrackerDjangoInstantiation(TestCase):
    """Test if backends are initialized properly from Django settings."""

    @override_settings(TRACKING_BACKENDS=SIMPLE_SETTINGS.copy())
    def test_django_simple_settings(self):
        """Test configuration of a simple backend"""

        backends = self._reload_backends()

        self.assertEqual(len(backends), 1)

        tracker.send({})

        self.assertEqual(backends.values()[0].count, 1)

    @override_settings(TRACKING_BACKENDS=MULTI_SETTINGS.copy())
    def test_django_multi_settings(self):
        """Test if multiple backends can be configured properly."""

        backends = self._reload_backends().values()

        self.assertEqual(len(backends), 2)

        event_count = 10
        for _ in xrange(event_count):
            tracker.send({})

        self.assertEqual(backends[0].count, event_count)
        self.assertEqual(backends[1].count, event_count)

    @override_settings(TRACKING_BACKENDS=MULTI_SETTINGS.copy())
    def test_django_remove_settings(self):
        """Test if a backend can be remove by setting it to None."""

        settings.TRACKING_BACKENDS.update({'second': None})

        backends = self._reload_backends()

        self.assertEqual(len(backends), 1)

    def _reload_backends(self):
        # pylint: disable=protected-access

        # Reset backends
        tracker._initialize_backends_from_django_settings()

        return tracker.backends


class DummyBackend(BaseBackend):
    def __init__(self, **options):
        super(DummyBackend, self).__init__(**options)
        self.flag = options.get('flag', False)
        self.count = 0

    def send(self, event):
        self.count += 1

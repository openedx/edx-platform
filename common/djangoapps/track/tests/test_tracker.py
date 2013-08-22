from django.test import TestCase
from django.test.utils import override_settings

import track.tracker as tracker
from track.backends.base import BaseBackend


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
    def setUp(self):
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
    """Test if backends are initialized properly from Django settings"""

    @override_settings(EVENT_TRACKERS=SIMPLE_SETTINGS)
    def test_django_simple_settings(self):
        """Test configuration of a simple backend"""

        # Reset backends
        tracker._initialize_backends_from_django_settings()

        backends = tracker._backends

        self.assertEqual(len(backends), 1)

        tracker.send({})

        self.assertEqual(backends.values()[0].count, 1)

    @override_settings(EVENT_TRACKERS=MULTI_SETTINGS)
    def test_django_multi_settings(self):
        """Test if backends are configured properly if there are multiple"""

        # Reset backends
        tracker._initialize_backends_from_django_settings()

        backends = tracker._backends.values()

        self.assertEqual(len(backends), 2)

        event_count = 10
        for _ in xrange(event_count):
            tracker.send({})

        self.assertEqual(backends[0].count, event_count)
        self.assertEqual(backends[1].count, event_count)


class DummyBackend(BaseBackend):
    def __init__(self, **options):
        super(DummyBackend, self).__init__(**options)
        self.flag = options.get('flag', False)
        self.count = 0

    def send(self, event):
        self.count += 1

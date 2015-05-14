from __future__ import absolute_import

from django.test import TestCase

from track.backends.django import DjangoBackend, TrackingLog


class TestDjangoBackend(TestCase):
    def setUp(self):
        super(TestDjangoBackend, self).setUp()
        self.backend = DjangoBackend()

    def test_django_backend(self):
        event = {
            'username': 'test',
            'time': '2013-01-01T12:01:00-05:00'
        }
        self.backend.send(event)

        results = list(TrackingLog.objects.all())

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, 'test')

        # Check if time is stored in UTC
        self.assertEqual(str(results[0].time), '2013-01-01 17:01:00+00:00')

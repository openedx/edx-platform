"""Test for async task service status"""

from django.utils import unittest
from django.test.client import Client
from django.core.urlresolvers import reverse
import json


class CeleryConfigTest(unittest.TestCase):
    """
    Test that we can get a response from Celery
    """

    def setUp(self):
        """
        Create a django test client
        """
        super(CeleryConfigTest, self).setUp()
        self.client = Client()
        self.ping_url = reverse('status.service.celery.ping')

    def test_ping(self):
        """
        Try to ping celery.
        """

        # Access the service status page, which starts a delayed
        # asynchronous task
        response = self.client.get(self.ping_url)

        # HTTP response should be successful
        self.assertEqual(response.status_code, 200)

        # Expect to get a JSON-serialized dict with
        # task and time information
        result_dict = json.loads(response.content)

        # Was it successful?
        self.assertTrue(result_dict['success'])

        # We should get a "pong" message back
        self.assertEqual(result_dict['value'], "pong")

        # We don't know the other dict values exactly,
        # but we can assert that they take the right form
        self.assertIsInstance(result_dict['task_id'], unicode)
        self.assertIsInstance(result_dict['time'], float)
        self.assertTrue(result_dict['time'] > 0.0)

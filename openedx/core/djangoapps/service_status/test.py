"""Test for async task service status"""


import json
import unittest

from django.test.client import Client
from django.urls import reverse


class CeleryConfigTest(unittest.TestCase):
    """
    Test that we can get a response from Celery
    """

    def setUp(self):
        """
        Create a django test client
        """
        super().setUp()
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
        assert response.status_code == 200

        # Expect to get a JSON-serialized dict with
        # task and time information
        result_dict = json.loads(response.content.decode('utf-8'))

        # Was it successful?
        assert result_dict['success']

        # We should get a "pong" message back
        assert result_dict['value'] == 'pong'

        # We don't know the other dict values exactly,
        # but we can assert that they take the right form
        assert isinstance(result_dict['task_id'], str)
        assert isinstance(result_dict['time'], float)
        assert result_dict['time'] > 0.0

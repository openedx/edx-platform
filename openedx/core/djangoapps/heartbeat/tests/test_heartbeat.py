"""
Test the heartbeat
"""


import json
from unittest.mock import patch

from django.db.utils import DatabaseError
from django.test.client import Client
from django.urls import reverse

from xmodule.exceptions import HeartbeatFailure
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class HeartbeatTestCase(ModuleStoreTestCase):
    """
    Test the heartbeat
    """

    def setUp(self):
        self.client = Client()
        self.heartbeat_url = reverse('heartbeat')
        return super().setUp()

    def test_success(self):
        response = self.client.get(self.heartbeat_url + '?extended')
        print(response)

        assert response.status_code == 200

    def test_sql_fail(self):
        with patch('openedx.core.djangoapps.heartbeat.default_checks.connection') as mock_connection:
            mock_connection.cursor.return_value.execute.side_effect = DatabaseError
            response = self.client.get(self.heartbeat_url)
            assert response.status_code == 503
            response_dict = json.loads(response.content.decode('utf-8'))
            assert 'sql' in response_dict

    def test_modulestore_fail(self):
        with patch('openedx.core.djangoapps.heartbeat.default_checks.modulestore') as mock_modulestore:
            mock_modulestore.return_value.heartbeat.side_effect = HeartbeatFailure('msg', 'service')
            response = self.client.get(self.heartbeat_url)
            assert response.status_code == 503

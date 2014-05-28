"""
Test the heartbeat
"""
from django.test.client import Client
from django.core.urlresolvers import reverse
import json
from django.db.utils import DatabaseError
import mock
from django.test.utils import override_settings
from django.conf import settings
from django.test.testcases import TestCase
from xmodule.modulestore.tests.django_utils import draft_mongo_store_config

TEST_MODULESTORE = draft_mongo_store_config(settings.TEST_ROOT / "data")

@override_settings(MODULESTORE=TEST_MODULESTORE)
class HeartbeatTestCase(TestCase):
    """
    Test the heartbeat
    """

    def setUp(self):
        self.client = Client()
        self.heartbeat_url = reverse('heartbeat')
        return super(HeartbeatTestCase, self).setUp()

    def tearDown(self):
        return super(HeartbeatTestCase, self).tearDown()

    def test_success(self):
        response = self.client.get(self.heartbeat_url)
        self.assertEqual(response.status_code, 200)

    def test_sql_fail(self):
        with mock.patch('heartbeat.views.connection') as mock_connection:
            mock_connection.cursor.return_value.execute.side_effect = DatabaseError
            response = self.client.get(self.heartbeat_url)
            self.assertEqual(response.status_code, 503)
            response_dict = json.loads(response.content)
            self.assertIn('SQL', response_dict)

    def test_mongo_fail(self):
        with mock.patch('pymongo.MongoClient.alive', return_value=False):
            response = self.client.get(self.heartbeat_url)
            self.assertEqual(response.status_code, 503)

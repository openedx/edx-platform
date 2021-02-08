import json
import requests
from mock import ANY, patch
from django.conf import settings
from django.test import override_settings, TestCase
from student.tests.factories import UserFactory

from mailchimp_pipeline.client import ChimpClient, Connection
from mailchimp_pipeline.tests.helpers import generate_mailchimp_url


class MailchimpPipelineClientTestClass(TestCase):
    """
        Tests for tasks ChimpClient and Connection
    """

    def setUp(self):
        super(MailchimpPipelineClientTestClass, self).setUp()
        self.mailchimp_list_id = settings.MAILCHIMP_LEARNERS_LIST_ID
        patcher = patch('mailchimp_pipeline.client.request', autospec=True)
        self.mock_request = patcher.start()
        self.mock_request.status_code = 204
        self.addCleanup(patcher.stop)
        self.user = UserFactory(is_staff=False, password='test')
        self.client = ChimpClient()
        self.connection = Connection.get_connection()
        self.mail_chimp_root_url = self.connection.root

    def test_get_list_members(self):
        """
            Test if the get_list_members function is sending `GET` request to the exact
            MailChimp URL
        """
        self.client.get_list_members(self.mailchimp_list_id)
        expected_url = "{root_url}list/{list_id}/members/".format(
            root_url=self.mail_chimp_root_url, list_id=self.mailchimp_list_id)
        self.mock_request.assert_called_with(
            "GET", url=expected_url, headers=ANY, data={}, auth=ANY, params=None)

    def test_delete_user_from_list(self):
        """
            Test if the delete_user_from_list function is sending `DELETE` request to the exact
            MailChimp URL
        """
        self.client.delete_user_from_list(self.mailchimp_list_id, self.user.email)
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        self.mock_request.assert_called_with(
            "DELETE", url=expected_url, headers=ANY, data={}, auth=ANY, params=None)

    def test_add_list_members_in_batch(self):
        """
            Test if the add_list_members_in_batch function is sending `POST` request to the exact
            MailChimp URL
        """
        data = {'data': 'some_data'}
        self.client.add_list_members_in_batch(self.mailchimp_list_id, data=data)
        expected_url = '{root_url}/lists/{list_id}'.format(
            root_url=self.mail_chimp_root_url, list_id=self.mailchimp_list_id)
        self.mock_request.assert_called_with(
            'POST', url=expected_url, data=json.dumps(data), params=None, auth=ANY, headers=ANY)

    def test_make_request_for_empty_path(self):
        """
            Test if the make_request function is sending `GET` request to the MailChimp root URL if a
            given path is None
        """
        self.connection.make_request()
        self.mock_request.assert_called_with('GET', url=self.mail_chimp_root_url, data={}, params=None, auth=ANY, headers=ANY)

    def test_make_request_for_404_response_status(self):
        """
            Test if the make_request function of client do not create exception and return None on
            response status code of 404
        """
        self.mock_request.return_value.status_code = 404
        self.mock_request.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError
        self.mock_request.return_value.json.return_value = {"status": 404}
        assert self.connection.make_request() is None

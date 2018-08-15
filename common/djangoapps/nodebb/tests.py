import mock

from django.contrib.auth.models import User
from django.test import TestCase
from djcelery.models import TaskState
from requests.exceptions import ConnectionError

from common.lib.nodebb_client.client import NodeBBClient
from tasks import task_create_user_on_nodebb


class NodeBBUserCreationTestCase(TestCase):
    def test_user_creation(self):
        username = "testuser"
        try:
            with mock.patch('common.lib.nodebb_client.users.ForumUser.create', side_effect=ConnectionError):
                NodeBBClient().users.create(
                    username=username,
                    kwargs={}
                )
        except ConnectionError:
            with mock.patch('common.lib.nodebb_client.users.ForumUser.create') as create_method:
                task_create_user_on_nodebb.apply_async(username=username, kwargs={})

                create_method.assert_called_with(username=username, kwargs={})

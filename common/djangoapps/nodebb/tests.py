import mock

from django.test import TestCase
from requests.exceptions import ConnectionError

from common.lib.nodebb_client.client import NodeBBClient
from tasks import (task_create_user_on_nodebb, task_update_user_profile_on_nodebb, task_delete_user_on_nodebb,
                   task_activate_user_on_nodebb, task_join_group_on_nodebb, task_update_onboarding_surveys_status)


class NodeBBUserCreationTestCase(TestCase):
    def test_user_creation(self):
        username = "testuser"
        try:
            with mock.patch('common.lib.nodebb_client.users.ForumUser.create', side_effect=ConnectionError):
                NodeBBClient().users.create(
                    username=username,
                    user_data={}
                )
        except ConnectionError:
            with mock.patch('nodebb.tests.task_create_user_on_nodebb.delay') as method:
                task_create_user_on_nodebb.delay(username=username, user_data={})

                method.assert_called_with(username=username, user_data={})

    def test_user_profile_update(self):
        username = 'testuser'
        data_to_sync = {
            'email': 'testuser@test.com',
            'first_name': 'test',
            'last_name': 'user'
        }
        try:
            with mock.patch('common.lib.nodebb_client.users.ForumUser.update_profile', side_effect=ConnectionError):
                NodeBBClient().users.update_profile(
                    username=username,
                    profile_data=data_to_sync
                )
        except ConnectionError:
            with mock.patch('nodebb.tasks.task_update_user_profile_on_nodebb.delay') as method:
                task_update_user_profile_on_nodebb.delay(username=username, profile_data=data_to_sync)

                method.assert_called_with(username=username, profile_data=data_to_sync)

    def test_user_deletion(self):
        username = "testuser"
        nodebb_client = NodeBBClient()
        try:
            with mock.patch('common.lib.nodebb_client.users.ForumUser.delete', side_effect=ConnectionError):
                nodebb_client.users.delete_user(username=username)
        except ConnectionError:
            with mock.patch('nodebb.tests.task_delete_user_on_nodebb.delay') as method:
                task_delete_user_on_nodebb.delay(username=username, kwargs={})

                method.assert_called_with(username=username, kwargs={})

    def test_user_activation(self):
        username = "testuser"
        active = True
        try:
            with mock.patch('common.lib.nodebb_client.users.ForumUser.activate', side_effect=ConnectionError):
                NodeBBClient().users.activate(
                    username=username,
                    active=active,
                    kwargs={}
                )
        except ConnectionError:
            with mock.patch('nodebb.tests.task_activate_user_on_nodebb.delay') as method:
                task_activate_user_on_nodebb.delay(username=username, active=active, kwargs={})

                method.assert_called_with(username=username, active=active, kwargs={})

    def test_user_join_on_nodebb(self):
        username = "testuser"
        category_id = "test_id"
        try:
            with mock.patch('common.lib.nodebb_client.users.ForumUser.join', side_effect=ConnectionError):
                with self.assertRaises(ConnectionError):
                    NodeBBClient().users.join(
                        category_id=category_id,
                        username=username,
                        kwargs={}
                    )
        except ConnectionError:
            with mock.patch('nodebb.tests.task_join_group_on_nodebb.delay') as method:
                task_join_group_on_nodebb.delay(category_id=category_id, username=username, kwargs={})

                method.assert_called_with(category_id=category_id, username=username, kwargs={})

    def test_update_onboarding_surveys_status(self):
        username = "testuser"
        try:
            with mock.patch(
                'common.lib.nodebb_client.users.ForumUser.update_onboarding_surveys_status',
                side_effect=ConnectionError
            ):
                with self.assertRaises(ConnectionError):
                    NodeBBClient().users.update_onboarding_surveys_status(username=username)
        except ConnectionError:
            with mock.patch(
                'nodebb.tests.task_update_onboarding_surveys_status.delay'
            ) as method:
                task_update_onboarding_surveys_status.delay(username=username)

                method.assert_called_with(username=username)

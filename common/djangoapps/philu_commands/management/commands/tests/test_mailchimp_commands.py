from __future__ import unicode_literals

import logging

import mock
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db.models.signals import post_save
from django.test import TestCase
from factory.django import mute_signals
from lms.djangoapps.onboarding.tests.factories import OrganizationFactory, UserFactory
from philu_commands.management.commands.sync_users_with_mailchimp import Command

log = logging.getLogger(__name__)
logging.disable(logging.NOTSET)
log.setLevel(logging.DEBUG)


class MailChimpUser(TestCase):
    """
        Tests for both `sync_users_with_mailchimp` and `delete_users_from_mailchimp` command.
    """

    @mute_signals(post_save)
    def setUp(self):
        super(MailChimpUser, self).setUp()
        self.user = UserFactory.create(
            username="test",
            password="test123",
            email="test@example.com"
        )
        org = OrganizationFactory()
        org.org_type = "New"
        org.save()
        self.user.extended_profile.organization = org
        self.user.extended_profile.save()

    @mock.patch('mailchimp_pipeline.client.ChimpClient.delete_user_from_list')
    def test_delete_users_from_mailchimp_command(self, mock_func):
        """
        This test checks the delete_user_from_mailchimp command.
        :param mock_func: Mocked Function to be tested.
        """
        call_command('delete_users_from_mailchimp')
        mock_func.assert_called_once_with(settings.MAILCHIMP_LEARNERS_LIST_ID, self.user.email)

    @mock.patch('mailchimp_pipeline.client.ChimpClient.add_list_members_in_batch')
    @mock.patch('philu_commands.management.commands.sync_users_with_mailchimp.connection')
    def test_sync_users_with_mailchimp_command(self, mocked_connection, mock_func):
        """
        This test checks the sync_user_with_mailchimp_command for with accurate data and check whether command pass the
        data to mailchimp accurately or not.
        :param mocked_connection: Mocked connection to handle the Database Cursor.
        :param mock_func: Mocked function which is responsible for sending data to mailchimp this function is to be
                            tested.
        """
        users = list(User.objects.all())
        users_data = Command().get_users_data_to_send(users)
        call_command('sync_users_with_mailchimp')
        mock_func.assert_called_once_with(settings.MAILCHIMP_LEARNERS_LIST_ID, {
            'members': users_data,
            'update_existing': True
        })

    @mock.patch('lms.djangoapps.certificates.api.get_certificates_for_user')
    @mock.patch('mailchimp_pipeline.client.ChimpClient.add_list_members_in_batch')
    @mock.patch('philu_commands.management.commands.sync_users_with_mailchimp.connection')
    def test_sync_users_with_mailchimp_command_for_cert_exception(self, mocked_connection, mock_func,
                                                                  mocked_get_user_cert_func):
        """
        This test is responsible for creating Exception while getting certificate data for user. This test covers the
        except part of User Certificate Gathering.
        :param mocked_connection: Mocked connection to handle the Database Cursor.
        :param mock_func: Mocked function which is responsible for sending data to mailchimp this function is to be
                            tested.
        :param mocked_get_user_cert_func: Mocked function to Raise Exception in command.
        :return:
        """
        mocked_get_user_cert_func.side_effect = Exception
        users = list(User.objects.all())
        users_data = Command().get_users_data_to_send(users)
        call_command('sync_users_with_mailchimp')
        mock_func.assert_called_once_with(settings.MAILCHIMP_LEARNERS_LIST_ID, {
            'members': users_data,
            'update_existing': True
        })
        self.assertRaises(Exception)

    @mock.patch('philu_commands.management.commands.sync_users_with_mailchimp.connection')
    def test_sync_users_with_mailchimp_command_for_exception(self, mocked_connection):
        """
        This test case is responsible for generating exception in the main try and except block in handle function of
        command and check the except block. We have not mocked the mailchimp function so in testing environment whenever
        we will call mailchimp function it will return exception.
        :param mocked_connection: Mocked connection to handle the Database Cursor.
        """
        call_command('sync_users_with_mailchimp')
        self.assertRaises(Exception)

    @mock.patch('philu_commands.management.commands.sync_users_with_mailchimp.get_user_active_enrollements')
    @mock.patch('philu_commands.management.commands.sync_users_with_mailchimp.connection')
    def test_sync_users_with_mailchimp_command_for_user_exception(self, mocked_connection, mocked_user_enrollment_func):
        """
        This test is responsible for creating Exception while getting data for user. This test covers the
        except part of User Data Gathering.
        :param mocked_connection: Mocked connection to handle the Database Cursor.
        :param mocked_user_enrollment_func: Mocked function to Raise Exception in command.
        """
        mocked_user_enrollment_func.side_effect = Exception
        call_command('sync_users_with_mailchimp')
        self.assertRaises(Exception)

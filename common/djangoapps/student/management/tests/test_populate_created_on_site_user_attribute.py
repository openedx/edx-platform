"""
Unittests for populate_created_on_site_user_attribute management command.
"""
from __future__ import absolute_import

import ddt
import mock
from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.test import TestCase
from six.moves import range

from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from student.models import Registration, UserAttribute
from student.tests.factories import UserFactory

CREATED_ON_SITE = 'created_on_site'


@ddt.ddt
class TestPopulateUserAttribute(SiteMixin, TestCase):
    """
    Test populate_created_on_site_user_attribute management command.
    """

    def setUp(self):
        super(TestPopulateUserAttribute, self).setUp()

        self._create_sample_data()
        self.users = User.objects.all()
        self.registered_users = Registration.objects.all()
        self.user_ids = ','.join([str(user.id) for user in self.users])
        self.activation_keys = ','.join([registered_user.activation_key for registered_user in self.registered_users])

    def _create_sample_data(self):
        """
        Creates the users and register them.
        """
        for __ in range(3):
            Registration().register(UserFactory.create())

    def test_command_by_user_ids(self):
        """
        Test population of created_on_site attribute by user ids.
        """
        call_command(
            "populate_created_on_site_user_attribute",
            "--users", self.user_ids,
            "--site-domain", self.site.domain
        )

        for user in self.users:
            self.assertEqual(UserAttribute.get_user_attribute(user, CREATED_ON_SITE), self.site.domain)

        # Populate 'created_on_site' attribute with different site domain
        call_command(
            "populate_created_on_site_user_attribute",
            "--users", self.user_ids,
            "--site-domain", self.site_other.domain
        )

        for user in self.users:
            # 'created_on_site' attribute already exists. Attribute's value will not change
            self.assertNotEqual(UserAttribute.get_user_attribute(user, CREATED_ON_SITE), self.site_other.domain)

    def test_command_by_activation_keys(self):
        """
        Test population of created_on_site attribute by activation keys.
        """
        call_command(
            "populate_created_on_site_user_attribute",
            "--activation-keys", self.activation_keys,
            "--site-domain", self.site.domain
        )

        for register_user in self.registered_users:
            self.assertEqual(UserAttribute.get_user_attribute(register_user.user, CREATED_ON_SITE), self.site.domain)

        # Populate 'created_on_site' attribute with different site domain
        call_command(
            "populate_created_on_site_user_attribute",
            "--activation-keys", self.activation_keys,
            "--site-domain", self.site_other.domain
        )

        for register_user in self.registered_users:
            # 'created_on_site' attribute already exists. Attribute's value will not change
            self.assertNotEqual(
                UserAttribute.get_user_attribute(register_user.user, CREATED_ON_SITE),
                self.site_other.domain
            )

    def test_command_with_incomplete_argument(self):
        """
        Test management command raises CommandError without '--users' and '--activation_keys' arguments.
        """
        with self.assertRaises(CommandError):
            call_command(
                "populate_created_on_site_user_attribute",
                "--site-domain", self.site.domain
            )

    def test_command_with_invalid_arguments(self):
        """
        Test management command with invalid user ids and activation keys.
        """
        user = self.users[0]
        call_command(
            "populate_created_on_site_user_attribute",
            "--users", '9{id}'.format(id=user.id),  # invalid id
            "--site-domain", self.site.domain
        )
        self.assertIsNone(UserAttribute.get_user_attribute(user, CREATED_ON_SITE))

        register_user = self.registered_users[0]
        call_command(
            "populate_created_on_site_user_attribute",
            "--activation-keys", "invalid-{key}".format(key=register_user.activation_key),  # invalid key
            "--site-domain", self.site.domain
        )
        self.assertIsNone(UserAttribute.get_user_attribute(register_user.user, CREATED_ON_SITE))

    def test_command_without_site_domain(self):
        """
        Test management command raises CommandError without '--site-domain' argument.
        """
        with self.assertRaises(CommandError):
            call_command(
                "populate_created_on_site_user_attribute",
                "--user", self.user_ids,
                "--activation-keys", self.activation_keys
            )

    @ddt.data('y', 'n')
    def test_with_invalid_site_domain(self, populate):
        """
        Test management command with invalid site domain.
        """
        fake_site_domain = 'fake-site-domain'
        with mock.patch('six.moves.input', return_value=populate):
            call_command(
                "populate_created_on_site_user_attribute",
                "--users", self.user_ids,
                "--site-domain", fake_site_domain
            )

        for user in self.users:
            if populate == 'y':
                self.assertEqual(UserAttribute.get_user_attribute(user, CREATED_ON_SITE), fake_site_domain)
            else:
                self.assertIsNone(UserAttribute.get_user_attribute(user, CREATED_ON_SITE))

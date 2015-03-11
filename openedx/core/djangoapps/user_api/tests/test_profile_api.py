# -*- coding: utf-8 -*-
""" Tests for the profile API. To be moved to new location. """
from django.contrib.auth.models import User
from django.test import TestCase

from ..accounts.api import get_account_settings
from ..api import account as account_api


class CreateAccountTest(TestCase):

    USERNAME = u'frank-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'frank+underwood@example.com'

    def test_create_profile(self):
        # Create a new account, which should have an empty profile by default.
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Retrieve the account settings
        user = User.objects.get(username=self.USERNAME)
        account_settings = get_account_settings(user)

        # Expect a date joined field but remove it to simplify the following comparison
        self.assertIsNotNone(account_settings['date_joined'])
        del account_settings['date_joined']

        # Expect all the values to be defaulted
        self.assertEqual(account_settings, {
            'username': self.USERNAME,
            'email': self.EMAIL,
            'name': u'',
            'gender': None,
            'language': u'',
            'goals': None,
            'level_of_education': None,
            'mailing_address': None,
            'year_of_birth': None,
            'country': None,
        })

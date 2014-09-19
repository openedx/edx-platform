# -*- coding: utf-8 -*-
""" Tests for the profile API. """


from django.test import TestCase
import ddt
from user_api.api import account as account_api
from user_api.api import profile as profile_api


@ddt.ddt
class ProfileApiTest(TestCase):

    USERNAME = u"Ḟṛäṅḳ"
    PASSWORD = u"ṕáśśẃőŕd"
    EMAIL = u"fŕáńḱ@éxáḿṕĺé.ćőḿ"

    def test_create_profile(self):
        # Create a new account, which should have an empty profile by default.
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Retrieve the profile, expecting default values
        profile = profile_api.profile_info(username=self.USERNAME)
        self.assertEqual(profile, {
            'username': self.USERNAME,
            'email': self.EMAIL,
            'full_name': u'',
        })

    def test_retrieve_profile_email(self):
        # We're implicitly testing username retrieval elsewhere,
        # so this test only covers retrieval by email
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        profile = profile_api.profile_info(email=self.EMAIL)
        self.assertEqual(profile['username'], self.USERNAME)
        self.assertEqual(profile['email'], self.EMAIL)

    @ddt.data(
        (None, ''),
        ('', ''),
        (u'ȻħȺɍłɇs', u'ȻħȺɍłɇs'),
        (u'𝓐' * 256, u'𝓐' * 255)
    )
    @ddt.unpack
    def test_update_full_name(self, new_full_name, expected_name):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        profile_api.update_profile(self.USERNAME, full_name=new_full_name)

        profile = profile_api.profile_info(username=self.USERNAME)
        self.assertEqual(profile['full_name'], expected_name)

    def test_retrieve_profile_no_kwargs(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Try to retrieve the profile, but don't provide the required args
        with self.assertRaises(profile_api.ProfileRequestError):
            profile_api.profile_info()

    def test_retrieve_profile_no_user(self):
        profile = profile_api.profile_info(username="does not exist")
        self.assertIs(profile, None)

        profile = profile_api.profile_info(email="does@not.exist")
        self.assertIs(profile, None)


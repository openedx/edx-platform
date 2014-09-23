# -*- coding: utf-8 -*-
""" Tests for student profile views. """

from urllib import urlencode
from mock import patch
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from user_api.api import account as account_api
from user_api.api import profile as profile_api


@patch.dict(settings.FEATURES, {'ENABLE_NEW_DASHBOARD': True})
class StudentProfileViewTest(TestCase):
    """ Tests for the student profile views. """

    USERNAME = u"heisenberg"
    PASSWORD = u"ḅḷüëṡḳÿ"
    EMAIL = u"walt@savewalterwhite.com"
    FULL_NAME = u"𝖂𝖆𝖑𝖙𝖊𝖗 𝖂𝖍𝖎𝖙𝖊"

    def setUp(self):
        # Create/activate a new account
        activation_key = account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        account_api.activate_account(activation_key)

        # Login
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result)

    def test_index(self):
        response = self.client.get(reverse('profile_index'))
        self.assertContains(response, "Student Profile")

    def test_name_change_handler(self):
        # Verify that the name on the account is blank
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['full_name'], '')

        response = self.client.put(
            path=reverse('name_change'),
            data=urlencode({
                # We can't pass a Unicode object to urlencode, so we encode the Unicode object
                'new_name': self.FULL_NAME.encode('utf8')
            }),
            content_type= 'application/x-www-form-urlencoded'
        )
        self.assertEquals(response.status_code, 204)

        # Verify that the name on the account has been changed
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['full_name'], self.FULL_NAME)

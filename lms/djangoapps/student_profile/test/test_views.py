# -*- coding: utf-8 -*-
""" Tests for student profile views. """

from urllib import urlencode
from mock import patch
import ddt
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from util.testing import UrlResetMixin
from user_api.api import account as account_api
from user_api.api import profile as profile_api


@ddt.ddt
class StudentProfileViewTest(UrlResetMixin, TestCase):
    """ Tests for the student profile views. """

    USERNAME = u"heisenberg"
    PASSWORD = u"ḅḷüëṡḳÿ"
    EMAIL = u"walt@savewalterwhite.com"
    FULL_NAME = u"𝖂𝖆𝖑𝖙𝖊𝖗 𝖂𝖍𝖎𝖙𝖊"

    @patch.dict(settings.FEATURES, {'ENABLE_NEW_DASHBOARD': True})
    def setUp(self):
        super(StudentProfileViewTest, self).setUp()

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

        response = self._change_name(self.FULL_NAME)
        self.assertEquals(response.status_code, 204)

        # Verify that the name on the account has been changed
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['full_name'], self.FULL_NAME)

    def test_name_change_invalid(self):
        # Name cannot be an empty string
        response = self._change_name('')
        self.assertEquals(response.status_code, 400)

    @ddt.data(
        ('get', 'profile_index'),
        ('put', 'name_change')
    )
    @ddt.unpack
    def test_require_login(self, method, url_name):
        # Access the page while logged out
        self.client.logout()
        url = reverse(url_name)
        response = getattr(self.client, method)(url, follow=True)

        # Should have been redirected to the login page
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn('accounts/login?next=', response.redirect_chain[0][0])

    @ddt.data(
        ('get', 'profile_index'),
        ('put', 'name_change')
    )
    @ddt.unpack
    def test_require_http_method(self, correct_method, url_name):
        wrong_methods = {'get', 'put', 'post', 'head', 'options', 'delete'} - {correct_method}
        url = reverse(url_name)

        for method in wrong_methods:
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 405)

    def _change_name(self, new_name):
        """Request a name change.

        Returns:
            HttpResponse

        """
        return self.client.put(
            path=reverse('name_change'),
            data=urlencode({
                # We can't pass a Unicode object to urlencode, so we encode the Unicode object
                'new_name': new_name.encode('utf-8')
            }),
            content_type= 'application/x-www-form-urlencoded'
        )

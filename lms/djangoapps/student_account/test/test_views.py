# -*- coding: utf-8 -*-
""" Tests for student account views. """

from urllib import urlencode
from mock import patch
import ddt
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from user_api.api import account as account_api
from user_api.api import profile as profile_api


@patch.dict(settings.FEATURES, {'ENABLE_NEW_DASHBOARD': True})
@ddt.ddt
class StudentAccountViewTest(TestCase):
    """ Tests for the student account views. """

    USERNAME = u"heisenberg"
    PASSWORD = u"ḅḷüëṡḳÿ"
    OLD_EMAIL = u"walter@graymattertech.com"
    NEW_EMAIL = u"walt@savewalterwhite.com"

    def setUp(self):
        # Create/activate a new account
        activation_key = account_api.create_account(self.USERNAME, self.PASSWORD, self.OLD_EMAIL)
        account_api.activate_account(activation_key)

        # Login
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result)

    def test_index(self):
        response = self.client.get(reverse('account_index'))
        self.assertContains(response, "Student Account")

    def test_email_change_request_handler(self):
        response = self.client.put(
            path=reverse('email_change_request'),
            data=urlencode({
                # We can't pass a Unicode object to urlencode, so we encode the Unicode object
                'new-email': self.NEW_EMAIL,
                'password': self.PASSWORD.encode('utf8')
            }),
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEquals(response.status_code, 204)

        # Verify that the email associated with the account remains unchanged
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['email'], self.OLD_EMAIL)

    def test_email_change_confirmation_handler(self):
        # Get an email change activation key
        activation_key = account_api.request_email_change(self.USERNAME, self.NEW_EMAIL, self.PASSWORD)

        response = self.client.get(reverse('email_change_confirm', kwargs={'key': activation_key}))
        self.assertContains(response, "Email change successful")

        # Verify that the email associated with the account has changed
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['email'], self.NEW_EMAIL)

    @ddt.data(
        ('get', 'account_index'),
        ('put', 'email_change_request')
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
        ('get', 'account_index'),
        ('put', 'email_change_request')
    )
    @ddt.unpack
    def test_require_http_method(self, correct_method, url_name):
        wrong_methods = {'get', 'put', 'post', 'head', 'options', 'delete'} - {correct_method}
        url = reverse(url_name)

        for method in wrong_methods:
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 405)

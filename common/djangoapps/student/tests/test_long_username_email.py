# -*- coding: utf-8 -*-

import json
from django.test import TestCase
from django.core.urlresolvers import reverse


class TestLongUsernameEmail(TestCase):

    def setUp(self):
        super(TestLongUsernameEmail, self).setUp()
        self.url = reverse('create_account')
        self.url_params = {
            'username': 'username',
            'email': 'foo_bar' + '@bar.com',
            'name': 'foo bar',
            'password': '123',
            'terms_of_service': 'true',
            'honor_code': 'true',
        }

    def test_long_username(self):
        """
        Test username cannot be more than 30 characters long.
        """

        self.url_params['username'] = 'username' * 4
        response = self.client.post(self.url, self.url_params)

        # Status code should be 400.
        self.assertEqual(response.status_code, 400)

        obj = json.loads(response.content)
        self.assertEqual(
            obj['value'],
            "Username cannot be more than 30 characters long",
        )

    def test_long_email(self):
        """
        Test email cannot be more than 75 characters long.
        """

        self.url_params['email'] = '{0}@bar.com'.format('foo_bar' * 15)
        response = self.client.post(self.url, self.url_params)

        # Status code should be 400.
        self.assertEqual(response.status_code, 400)

        obj = json.loads(response.content)
        self.assertEqual(
            obj['value'],
            "Email cannot be more than 75 characters long",
        )

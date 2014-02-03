# -*- coding: utf-8 -*-
"""
This test file will verify functionality relating to changing language settings for a user
"""
from django.test import TestCase
from django.core.urlresolvers import reverse
from student.tests.factories import UserFactory


class TestLanguageSettings(TestCase):
    """
    Language settings tests
    """
    def setUp(self):
        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")

    def test_successful_language_change(self):
        # Esperanto is our dummy language
        post_data = dict(language='eo',)
        response = self.client.post('/i18n/setlang/', data=post_data)
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertEqual(session['django_language'], 'eo')

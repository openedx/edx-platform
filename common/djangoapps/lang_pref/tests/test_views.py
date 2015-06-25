"""
Tests for the language setting view
"""
from django.core.urlresolvers import reverse
from django.test import TestCase
from student.tests.factories import UserFactory
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from lang_pref import LANGUAGE_KEY


class TestLanguageSetting(TestCase):
    """
    Test setting languages
    """
    def test_set_preference_happy(self):
        user = UserFactory.create()
        self.client.login(username=user.username, password='test')

        lang = 'en'
        response = self.client.post(reverse('lang_pref_set_language'), {'language': lang})

        self.assertEquals(response.status_code, 200)
        user_pref = get_user_preference(user, LANGUAGE_KEY)
        self.assertEqual(user_pref, lang)

    def test_set_preference_missing_lang(self):
        user = UserFactory.create()
        self.client.login(username=user.username, password='test')

        response = self.client.post(reverse('lang_pref_set_language'))

        self.assertEquals(response.status_code, 400)

        self.assertIsNone(get_user_preference(user, LANGUAGE_KEY))

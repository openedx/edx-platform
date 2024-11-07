"""
Tests: lang pref views
"""


import json

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import get_language


class TestLangPrefView(TestCase):
    """
    Language preference view tests.
    """

    def test_language_update(self):
        # test language updating correctly.
        response = self.client.patch(reverse("update_language"), json.dumps({'pref-lang': 'eo'}))
        assert response.status_code == 200
        self.client.get('/')
        assert get_language() == 'eo'

        response = self.client.patch(reverse("update_language"), json.dumps({'pref-lang': 'en'}))
        assert response.status_code == 200
        self.client.get('/')
        assert get_language() == 'en'

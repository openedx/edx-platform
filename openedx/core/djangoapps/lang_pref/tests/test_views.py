"""
Tests: lang pref views
"""


import json

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.translation import LANGUAGE_SESSION_KEY, get_language
from common.djangoapps.student.tests.factories import UserFactory


class TestLangPrefView(TestCase):
    """
    Language preference view tests.
    """

    def setUp(self):
        super(TestLangPrefView, self).setUp()
        self.session_middleware = SessionMiddleware()
        self.user = UserFactory.create()
        self.request = RequestFactory().get('/somewhere')
        self.request.user = self.user
        self.session_middleware.process_request(self.request)

    def test_language_session_update(self):
        # test language session updating correctly.
        self.request.session[LANGUAGE_SESSION_KEY] = 'ar'
        response = self.client.patch(reverse("session_language"), json.dumps({'pref-lang': 'eo'}))
        self.assertEqual(response.status_code, 200)
        self.client.get('/')
        self.assertEqual(get_language(), 'eo')

        response = self.client.patch(reverse("session_language"), json.dumps({'pref-lang': 'en'}))
        self.assertEqual(response.status_code, 200)
        self.client.get('/')
        self.assertEqual(get_language(), 'en')

"""
Tests: lang pref views
"""
import json
from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from student.tests.factories import UserFactory
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.translation import get_language


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
        self.request.session[LANGUAGE_SESSION_KEY] = 'ar'  # pylint: disable=no-member
        response = self.client.patch(reverse("session_language"), json.dumps({'pref-lang': 'eo'}))
        self.assertEqual(response.status_code, 200)
        self.client.get('/')
        self.assertEquals(get_language(), 'eo')

        response = self.client.patch(reverse("session_language"), json.dumps({'pref-lang': 'en'}))
        self.assertEqual(response.status_code, 200)
        self.client.get('/')
        self.assertEquals(get_language(), 'en')

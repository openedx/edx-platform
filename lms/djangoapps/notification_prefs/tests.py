from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from mitxmako.middleware import MakoMiddleware
from student.tests.factories import UserFactory
from user_api.models import UserPreference
from notification_prefs import NOTIFICATION_PREF_KEY
from notification_prefs.views import ajax_enable, ajax_disable, unsubscribe


@override_settings(SECRET_KEY="test secret key")
class NotificationPrefViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure global state is set up appropriately
        Client().get("/")

    def setUp(self):
        self.user = UserFactory.create(username="testuser")
        # Username with length equal to AES block length to test padding
        self.aes_block_length_user = UserFactory.create(username="sixteencharsuser")
        # Tokens are intentionally hard-coded instead of computed to help us
        # avoid breaking existing links.
        self.tokens = {
            # Encrypted value: "testuser" + "\x08" * 8
            self.user: "DyYxCj3oVl9vVgq_VHlfqw==",
            # Encrypted value: "sixteencharsuser" + "\x10" * 16
            self.aes_block_length_user: "_E9YK4jYDL1MBMFWd_Dt4tRGw8HDEmlcLVFawgY9wI8=",
        }
        self.request_factory = RequestFactory()

    def create_prefs(self):
        for (user, token) in self.tokens.items():
            UserPreference.objects.create(user=user, key=NOTIFICATION_PREF_KEY, value=token)

    def assertPrefValid(self, user):
        self.assertEqual(
            UserPreference.objects.get(user=user, key=NOTIFICATION_PREF_KEY).value,
            self.tokens[user]
        )

    def assertNotPrefExists(self, user):
        self.assertFalse(
            UserPreference.objects.filter(user=user, key=NOTIFICATION_PREF_KEY).exists()
        )

    # AJAX enable view

    def test_ajax_enable_get(self):
        request = self.request_factory.get("dummy")
        request.user = self.user
        response = ajax_enable(request)
        self.assertEqual(response.status_code, 405)
        self.assertNotPrefExists(self.user)

    def test_ajax_enable_anon_user(self):
        request = self.request_factory.post("dummy")
        request.user = AnonymousUser()
        response = ajax_enable(request)
        self.assertEqual(response.status_code, 403)
        self.assertNotPrefExists(self.user)

    def test_ajax_enable_success(self):
        def test_user(user):
            request = self.request_factory.post("dummy")
            request.user = user
            response = ajax_enable(request)
            self.assertEqual(response.status_code, 204)
            self.assertPrefValid(user)

        test_user(self.user)
        test_user(self.aes_block_length_user)

    def test_ajax_enable_already_enabled(self):
        self.create_prefs()
        request = self.request_factory.post("dummy")
        request.user = self.user
        response = ajax_enable(request)
        self.assertEqual(response.status_code, 204)
        self.assertPrefValid(self.user)

    def test_ajax_enable_distinct_values(self):
        request = self.request_factory.post("dummy")
        request.user = self.user
        ajax_enable(request)
        other_user = UserFactory.create()
        request.user = other_user
        ajax_enable(request)
        self.assertNotEqual(
            UserPreference.objects.get(user=self.user, key=NOTIFICATION_PREF_KEY).value,
            UserPreference.objects.get(user=other_user, key=NOTIFICATION_PREF_KEY).value
        )

    # AJAX disable view

    def test_ajax_disable_get(self):
        self.create_prefs()
        request = self.request_factory.get("dummy")
        request.user = self.user
        response = ajax_disable(request)
        self.assertEqual(response.status_code, 405)
        self.assertPrefValid(self.user)

    def test_ajax_disable_anon_user(self):
        self.create_prefs()
        request = self.request_factory.post("dummy")
        request.user = AnonymousUser()
        response = ajax_disable(request)
        self.assertEqual(response.status_code, 403)
        self.assertPrefValid(self.user)

    def test_ajax_disable_success(self):
        self.create_prefs()
        request = self.request_factory.post("dummy")
        request.user = self.user
        response = ajax_disable(request)
        self.assertEqual(response.status_code, 204)
        self.assertNotPrefExists(self.user)

    def test_ajax_disable_already_disabled(self):
        request = self.request_factory.post("dummy")
        request.user = self.user
        response = ajax_disable(request)
        self.assertEqual(response.status_code, 204)
        self.assertNotPrefExists(self.user)

    # Unsubscribe view

    def test_unsubscribe_post(self):
        request = self.request_factory.post("dummy")
        response = unsubscribe(request, "dummy")
        self.assertEqual(response.status_code, 405)

    def test_unsubscribe_invalid_token(self):
        def test_invalid_token(token):
            request = self.request_factory.get("dummy")
            self.assertRaises(Http404, unsubscribe, request, token)

        # Invalid base64 encoding
        test_invalid_token("Non-ASCII\xff")
        test_invalid_token("ZOMG INVALID BASE64 CHARS!!!")
        test_invalid_token(self.tokens[self.user][:-1])

        # Token of wrong length
        test_invalid_token(self.tokens[self.user][:-4])

        # Invalid padding (ends in 0 byte)
        # Encrypted value: "testuser" + "\x00" * 8
        test_invalid_token("yhrNEjt48uMRZc3U3uR4vA==")

        # Invalid padding (ends in byte > 16)
        # Encrypted value: "testusertestuser"
        test_invalid_token("LqItcaGOQXK0mglIElnMng==")

        # Invalid padding (entire string is padding)
        # Encrypted value: "\x10" * 16
        test_invalid_token("1EbDwcMSaVwtUVrCBj3Ajw==")

        # Nonexistent user
        # Encrypted value: "nonexistentuser\x01"
        test_invalid_token("KnJTFMYitSOem5Sw2LuYBg==")

    def test_unsubscribe_success(self):
        self.create_prefs()

        def test_user(user):
            request = self.request_factory.get("dummy")
            request.user = AnonymousUser()
            response = unsubscribe(request, self.tokens[user])
            self.assertEqual(response.status_code, 200)
            self.assertNotPrefExists(user)

        test_user(self.user)
        test_user(self.aes_block_length_user)

    def test_unsubscribe_twice(self):
        self.create_prefs()
        request = self.request_factory.get("dummy")
        request.user = AnonymousUser()
        unsubscribe(request, self.tokens[self.user])
        response = unsubscribe(request, self.tokens[self.user])
        self.assertEqual(response.status_code, 200)
        self.assertNotPrefExists(self.user)

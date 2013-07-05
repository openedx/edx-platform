from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from notification_prefs import NOTIFICATION_PREF_KEY
from student.tests.factories import UserFactory
from user_api.models import UserPreference
from mailgun_webhook.views import unsubscribe


@override_settings(MAILGUN_API_KEY="key-1lmspg67fhkxg534xhdaxcxc4ua54fo6")
class MailgunUnsubscribeTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.request_factory = RequestFactory()
        self.valid_request_data = {
            "timestamp": "1373040880",
            "token": "3p662km24nm--z85hgk0f1cjhuvpdnyv1gy5b0lrpj34r48dz1",
            "signature": "3fb40b08fc7b1c57e1cfa616abb33cf5b613ea34801049147fb7742adda6ae82",
            "event": "unsubscribed",
            "recipient": self.user.email,
        }
        UserPreference.objects.create(user=self.user, key=NOTIFICATION_PREF_KEY)

    def get_pref_exists(self):
        return UserPreference.objects.filter(
            user=self.user,
            key=NOTIFICATION_PREF_KEY
        ).exists()

    @override_settings(MAILGUN_API_KEY=None)
    def test_mailgun_not_configured(self):
        request = self.request_factory.post("dummy", data=self.valid_request_data)
        response = unsubscribe(request)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(self.get_pref_exists())

    def test_get(self):
        request = self.request_factory.get("dummy", data=self.valid_request_data)
        response = unsubscribe(request)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.get_pref_exists())

    def test_missing_data(self):
        def test_case(key):
            data = self.valid_request_data.copy()
            del data[key]
            request = self.request_factory.post("dummy", data=data)
            response = unsubscribe(request)
            self.assertEqual(response.status_code, 400)
            self.assertTrue(self.get_pref_exists())

        test_case("timestamp")
        test_case("token")
        test_case("signature")
        test_case("event")
        test_case("recipient")

    def test_invalid_signature(self):
        data = self.valid_request_data.copy()
        data["signature"] = "not the right signature"
        request = self.request_factory.post("dummy", data=data)
        response = unsubscribe(request)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(self.get_pref_exists())

    def test_invalid_event(self):
        data = self.valid_request_data.copy()
        data["event"] = "clicked"
        request = self.request_factory.post("dummy", data=data)
        response = unsubscribe(request)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(self.get_pref_exists())

    def test_success(self):
        request = self.request_factory.post("dummy", data=self.valid_request_data)
        response = unsubscribe(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.get_pref_exists())

    def test_already_unsubscribed(self):
        UserPreference.objects.filter(user=self.user, key=NOTIFICATION_PREF_KEY).delete()
        request = self.request_factory.post("dummy", data=self.valid_request_data)
        response = unsubscribe(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.get_pref_exists())

    def test_invalid_email(self):
        data = self.valid_request_data.copy()
        data["recipient"] = "other@edx.org"
        request = self.request_factory.post("dummy", data=data)
        response = unsubscribe(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.get_pref_exists())

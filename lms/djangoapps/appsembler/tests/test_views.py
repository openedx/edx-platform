import ddt
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from rest_framework import status
import mock


@ddt.ddt
class TestUserSignup(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        #self.url = reverse('user_signup_endpoint')
        self.url = reverse('user_signup_endpoint_new')

    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_only_responds_to_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @ddt.data(
        ('', "Doe", "john@doe.com", "password", "secret_key", status.HTTP_400_BAD_REQUEST),  # no first name
        ('John', '', "john@doe.com", "password", "secret_key", status.HTTP_400_BAD_REQUEST),  # no last name
        ('John', 'Doe', "", "password", "secret_key", status.HTTP_400_BAD_REQUEST),  # no email
        ('John', 'Doe', "john@doe.com", "", "secret_key", status.HTTP_400_BAD_REQUEST),  # no password
        ('John', 'Doe', "john@doe.com", "password", "", status.HTTP_403_FORBIDDEN),  # no secret key
        ('John', 'Doe', "john@doe.com", "password", "wrong_secret_key", status.HTTP_403_FORBIDDEN),  # wrong secret key
    )
    @ddt.unpack
    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_fail_without_required_data(self, first_name, last_name, email, password, secret_key, status_code):
        payload = {'first_name': first_name,
                   'last_name': last_name,
                   'email': email,
                   'password': password,
                   'secret_key': secret_key}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status_code)

    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_creates_user_without_enrollment(self):
        payload = {'first_name': 'John',
                   'last_name': 'Doe',
                   'email': 'john@doe.com',
                   'password': 'password',
                   'secret_key': 'secret_key'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.filter(email="john@doe.com").count(), 1)

    def test_creates_enrolled_user(self):
        pass

import ddt
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
import mock


@ddt.ddt
class TestUserSignup(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse('user_signup_endpoint')

    def test_only_responds_to_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    @ddt.data(
        ('', "Doe", "john@doe.com", "password", "secret_key", 400),
        ('John', '', "john@doe.com", "password", "secret_key", 400),
        ('John', 'Doe', "john@doe.com", "", "secret_key", 400),
        ('John', 'Doe', "john@doe.com", "password", "", 403),
    )
    @ddt.unpack
    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_fail_without_required_data(self, first_name, last_name, email, password, secret_key, status_code):
        payload = {'FirstName': first_name,
                   'LastName': last_name,
                   'Email': email,
                   'Password': password,
                   'SecretKey': secret_key}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status_code)

    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_creates_user_without_enrollment(self):
        payload = {'FirstName': 'John',
                   'LastName': 'Doe',
                   'Email': 'john@doe.com',
                   'Password': 'password',
                   'SecretKey': 'secret_key'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

    def test_creates_enrolled_user(self):
        pass

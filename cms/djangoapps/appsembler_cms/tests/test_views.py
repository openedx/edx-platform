# to run just these tests:
# ./manage.py cms --settings test test cms/djangoapps/appsembler_cms/tests/test_views.py

import ddt
import mock
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from rest_framework import status

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@ddt.ddt
class TestUserSignup(ModuleStoreTestCase):
    def setUp(self):
        super(TestUserSignup, self).setUp()
        self.url = reverse('create_course_endpoint')

    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_only_responds_to_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_fails_for_nonexisting_user(self):
        payload = {
            'email': 'john@doe.com',
            'secret_key': 'secret_key'
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('User does not exist in academy.appsembler.com', response.content)

    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_creates_course_for_existing_user(self):
        user = UserFactory.create(username="JohnDoe", email="john@doe.com", password="password")
        self.assertEqual(User.objects.filter(username="JohnDoe").count(), 1)

        payload = {
           'email': 'john@doe.com',
           'secret_key': 'secret_key'
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('/course/AppsemblerX/JohnDoe101/CurrentTerm', response.content)

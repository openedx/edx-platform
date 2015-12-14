# to run just these tests:
# ./manage.py lms --settings test test lms/djangoapps/appsembler_lms/tests/test_views.py


import ddt
import mock
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.test import TestCase
from rest_framework import status

from student.models import CourseEnrollment
# from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory
from appsembler_lms.models import Organization


@ddt.ddt
class TestUserSignup(TestCase):
    def setUp(self):
        self.url = reverse('user_signup_endpoint')

    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_only_responds_to_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @ddt.data(
        ('', "john@doe.com", "password", "acme", "ACME Inc", "secret_key", status.HTTP_400_BAD_REQUEST),  # no name
        ('John Doe', "", "password", "acme", "ACME Inc", "secret_key", status.HTTP_400_BAD_REQUEST),  # no email
        ('John Doe', "john@doe.com", "", "acme", "ACME Inc", "secret_key", status.HTTP_400_BAD_REQUEST),  # no password
        ('John Doe', "john@doe.com", "password", "", "ACME Inc", "secret_key", status.HTTP_400_BAD_REQUEST),  # no org
        ('John Doe', "john@doe.com", "password", "acme", "", "secret_key", status.HTTP_400_BAD_REQUEST),  # no org name
        ('John Doe', "john@doe.com", "password", "acme", "ACME Inc", "", status.HTTP_403_FORBIDDEN),  # no secret key
        ('John Doe', "john@doe.com", "password", "acme", "ACME Inc", "wrong_secret_key", status.HTTP_403_FORBIDDEN),  # wrong secret key
    )
    @ddt.unpack
    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_fail_without_required_data(self, name, email, password, org, org_name, secret_key, status_code):
        payload = {'name': name,
                   'email': email,
                   'password': password,
                   'org':org,
                   'org_name':org_name,
                   'secret_key': secret_key}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status_code)

    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_creates_user_without_enrollment(self):
        payload = {'name': 'John Doe',
                   'email': 'john@doe.com',
                   'password': 'password',
                   'org': 'acme',
                   'org_name': 'ACME Inc',
                   'secret_key': 'secret_key'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('JohnDoe', response.content)
        self.assertEqual(User.objects.filter(email="john@doe.com").count(), 1)
        # it should create an organization
        self.assertEqual(Organization.objects.filter(key='acme').count(), 1)
        # and associate it with the user
        john = User.objects.get(email="john@doe.com")
        acme = Organization.objects.get(key='acme')
        self.assertEqual(john.profile.organization, acme)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, render_to_string('appsembler/emails/user_welcome_email_subject.txt'))
        self.assertIn('john@doe.com', mail.outbox[0].body)
        self.assertIn('password', mail.outbox[0].body)
        self.assertIn('John Doe', mail.outbox[0].body)
        # make sure user creation follows django 1.8 usage where last_login = None
        self.assertEqual(User.objects.get(email="john@doe.com").last_login, None)

    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_creates_unique_username_if_already_exists(self):
        User.objects.create(
            username="JohnDoe",
            email="test@email.com"
        )
        self.assertEqual(User.objects.filter(username="JohnDoe").count(), 1)

        payload = {'name': 'John Doe',
                   'email': 'john@doe.com',
                   'password': 'password',
                   'org': 'acme',
                   'org_name': 'ACME Inc',
                   'secret_key': 'secret_key'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('JohnDoe', response.content)
        self.assertEqual(User.objects.filter(username="JohnDoe1").count(), 1)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, render_to_string('appsembler/emails/user_welcome_email_subject.txt'))
        self.assertIn('john@doe.com', mail.outbox[0].body)
        self.assertIn('password', mail.outbox[0].body)
        self.assertIn('John Doe', mail.outbox[0].body)

    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_uses_existing_org(self):
        Organization.objects.create(key="acme", display_name="ACME Inc")
        self.assertEqual(Organization.objects.filter(key='acme').count(), 1)

        payload = {'name': 'Jane Doe',
                   'email': 'jane@doe.com',
                   'password': 'password',
                   'org': 'acme',
                   'org_name': 'ACME Inc',
                   'secret_key': 'secret_key'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organization.objects.all().count(), 1)
        organization = Organization.objects.get(key='acme')
        self.assertEqual(User.objects.filter(email='jane@doe.com').count(), 1)
        self.assertEqual(User.objects.get(email='jane@doe.com').profile.organization,
                         organization)



@ddt.ddt
class TestUserEnroll(ModuleStoreTestCase):
    def setUp(self):
        super(TestUserEnroll, self).setUp()
        self.course_key = ToyCourseFactory.create().id
        self.url = reverse('user_signup_endpoint')

    @mock.patch.dict(settings.FEATURES, {'APPSEMBLER_SECRET_KEY': 'secret_key'})
    def test_creates_enrolled_user(self):
        payload = {'name': 'John Doe',
                   'email': 'john@doe.com',
                   'password': 'password',
                   'org': 'acme',
                   'org_name': 'ACME Inc',
                   'secret_key': 'secret_key',
                   'course_id': 'edX/toy/2012_Fall'}
        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('JohnDoe', response.content)
        self.assertEqual(User.objects.filter(email="john@doe.com").count(), 1)

        user = User.objects.get(email=payload['email'])
        self.assertTrue(CourseEnrollment.is_enrolled(user=user, course_key=self.course_key))
        self.assertIn(payload['email'], response.content)
        self.assertIn('JohnDoe', response.content)
        self.assertIn('Toy Course', response.content)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, render_to_string('appsembler/emails/user_welcome_email_subject.txt'))
        self.assertIn('Toy Course', mail.outbox[0].body)
        self.assertIn('john@doe.com', mail.outbox[0].body)
        self.assertIn('password', mail.outbox[0].body)
        self.assertIn('John Doe', mail.outbox[0].body)


# class TestUserLogin(TestCase):
#     def setUp(self):
#         self.email = 'janedoe@example.com'
#         self.password = 'password'
#         self.user = UserFactory.create(username="janedoe", email=self.email,  password=self.password)
#
#     def test_login_pings_amc(self):
#         # For some reason, the last_login is not getting set here
#         self.user.last_login = None
#         response = self.client.post(reverse('user_api_login_session'), {'email':self.email, 'password': self.password})
#         self.assertEqual(response.status_code, 200)
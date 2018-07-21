import json

import ddt
from django.test import Client, TestCase
from django.urls import reverse

from lms.djangoapps.user_manager.models import UserManagerRole
from student.tests.factories import UserFactory


@ddt.ddt
class UserManagerRoleViewsTest(TestCase):

    def _create_users(self):
        for idx in range(10):
            username = 'report{}'.format(idx)
            email = '{username}@somecorp.com'.format(username=username)
            yield UserFactory(username=username, email=email)

    def _create_managers(self):
        for idx in range(2):
            username = 'manager{}'.format(idx)
            email = '{username}@somecorp.com'.format(username=username)
            yield UserFactory(username=username, email=email)

    def setUp(self):
        self.user = UserFactory(username='staff', is_staff=True)
        self.client = Client()
        self.client.login(username=self.user.username, password='test')
        self.users = list(self._create_users())
        self.managers = list(self._create_managers())
        for user in self.users[:5]:
            UserManagerRole.objects.create(manager_user=self.managers[0], user=user)
        for user in self.users[5:]:
            UserManagerRole.objects.create(manager_user=self.managers[1], user=user)

        UserManagerRole.objects.create(manager_user=self.managers[1], user=self.users[0])

    def test_no_duplicate_managers(self):
        response = self.client.get(reverse('user_manager_api:v1:managers-list'))
        data = json.loads(response.content)
        results = data['results']
        self.assertEqual(len(results), 2)

    @ddt.data('username', 'email')
    def test_manager_reports_list_get(self, attr):
        url = reverse(
            'user_manager_api:v1:manager-reports-list',
            kwargs={'username': getattr(self.managers[0], attr)},
        )
        response = self.client.get(url)
        data = json.loads(response.content)
        results = data['results']
        self.assertEqual(len(results), 5)

    def test_manager_reports_list_post_duplicate(self):
        url = reverse(
            'user_manager_api:v1:manager-reports-list',
            kwargs={'username': self.managers[0].email},
        )
        self.client.post(url, {'email': self.users[0].email})
        query = UserManagerRole.objects.filter(manager_user=self.managers[0])
        self.assertEqual(query.count(), 5)

    def test_manager_reports_list_post_nonexistent(self):
        url = reverse(
            'user_manager_api:v1:manager-reports-list',
            kwargs={'username': self.managers[0].email},
        )
        response = self.client.post(url, {'email': 'non@existent.com'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, '{"detail":"No user with that email"}')

    def test_manager_reports_list_delete(self):
        url = reverse(
            'user_manager_api:v1:manager-reports-list',
            kwargs={'username': self.managers[0].email},
        )
        self.client.delete(url)
        query = UserManagerRole.objects.filter(manager_user=self.managers[0])
        self.assertEqual(query.count(), 0)

    @ddt.data('username', 'email')
    def test_user_managers_list_get(self, attr):
        url = reverse(
            'user_manager_api:v1:user-managers-list',
            kwargs={'username': getattr(self.users[0], attr)},
        )
        response = self.client.get(url)
        data = json.loads(response.content)
        results = data['results']
        self.assertEqual(len(results), 2)

    def test_user_managers_list_post_duplicate(self):
        url = reverse(
            'user_manager_api:v1:user-managers-list',
            kwargs={'username': self.users[0].email},
        )
        self.client.post(url, {'email': self.managers[0].email})
        query = UserManagerRole.objects.filter(user=self.users[0])
        self.assertEqual(query.count(), 2)

    def test_user_managers_list_post_unregistered(self):
        url = reverse(
            'user_manager_api:v1:user-managers-list',
            kwargs={'username': self.users[0].email},
        )
        self.client.post(url, {'email': 'unregistered@user.com'})
        query = UserManagerRole.objects.filter(user=self.users[0])
        self.assertEqual(query.count(), 3)
        self.assertIn(
            'unregistered@user.com',
            query.values_list('unregistered_manager_email', flat=True),
        )

    def test_user_managers_list_delete(self):
        url = reverse(
            'user_manager_api:v1:user-managers-list',
            kwargs={'username': self.users[0].email},
        )
        self.client.delete(url)
        query = UserManagerRole.objects.filter(user=self.users[0])
        self.assertEqual(query.count(), 0)

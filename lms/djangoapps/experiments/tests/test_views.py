import urllib

from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase

from experiments.factories import ExperimentDataFactory
from experiments.models import ExperimentData
from experiments.serializers import ExperimentDataSerializer
from student.tests.factories import UserFactory


class ExperimentDataViewSetTests(APITestCase):
    def assert_data_created_for_user(self, user, method='post', status=201):
        url = reverse('api_experiments:v0:data-list')
        data = {
            'experiment_id': 1,
            'key': 'foo',
            'value': 'bar',
        }
        self.client.login(username=user.username, password=UserFactory._DEFAULT_PASSWORD)
        response = getattr(self.client, method)(url, data)
        self.assertEqual(response.status_code, status)

        # This will raise an exception if no data exists
        ExperimentData.objects.get(user=user)

        data['user'] = user.username
        self.assertDictContainsSubset(data, response.data)

    def test_list_permissions(self):
        """ Users should only be able to list their own data. """
        url = reverse('api_experiments:v0:data-list')
        user = UserFactory()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        ExperimentDataFactory()
        datum = ExperimentDataFactory(user=user)
        self.client.login(username=user.username, password=UserFactory._DEFAULT_PASSWORD)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], ExperimentDataSerializer([datum], many=True).data)

    def test_list_filtering(self):
        """ Users should be able to filter by the experiment_id and key fields. """
        url = reverse('api_experiments:v0:data-list')
        user = UserFactory()
        self.client.login(username=user.username, password=UserFactory._DEFAULT_PASSWORD)

        experiment_id = 1
        ExperimentDataFactory()
        ExperimentDataFactory(user=user)
        data = ExperimentDataFactory.create_batch(3, user=user, experiment_id=experiment_id)

        qs = urllib.urlencode({'experiment_id': experiment_id})
        response = self.client.get('{url}?{qs}'.format(url=url, qs=qs))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], ExperimentDataSerializer(data, many=True).data)

        datum = data[0]
        qs = urllib.urlencode({'key': datum.key})
        response = self.client.get('{url}?{qs}'.format(url=url, qs=qs))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], ExperimentDataSerializer([datum], many=True).data)

        qs = urllib.urlencode({'experiment_id': experiment_id, 'key': datum.key})
        response = self.client.get('{url}?{qs}'.format(url=url, qs=qs))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], ExperimentDataSerializer([datum], many=True).data)

    def test_read_permissions(self):
        """ Users should only be allowed to read their own data. """
        user = UserFactory()
        datum = ExperimentDataFactory(user=user)
        url = reverse('api_experiments:v0:data-detail', kwargs={'pk': datum.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.login(username=user.username, password=UserFactory._DEFAULT_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        other_user = UserFactory()
        self.client.login(username=other_user.username, password=UserFactory._DEFAULT_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_create_permissions(self):
        """ Users should only be allowed to create data for themselves. """
        url = reverse('api_experiments:v0:data-list')

        # Authentication is required
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 401)

        user = UserFactory()
        data = {
            'experiment_id': 1,
            'key': 'foo',
            'value': 'bar',
        }
        self.client.login(username=user.username, password=UserFactory._DEFAULT_PASSWORD)

        # Users can create data for themselves
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        ExperimentData.objects.get(user=user)

        # A non-staff user cannot create data for another user
        other_user = UserFactory()
        data['user'] = other_user.username
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ExperimentData.objects.filter(user=other_user).exists())

        # A staff user can create data for other users
        user.is_staff = True
        user.save()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        ExperimentData.objects.get(user=other_user)

    def test_put_as_create(self):
        """ Users should be able to use PUT to create new data. """
        user = UserFactory()
        self.assert_data_created_for_user(user, 'put')

        # Subsequent requests should update the data
        self.assert_data_created_for_user(user, 'put', 200)

    def test_update_permissions(self):
        """ Users should only be allowed to update their own data. """
        user = UserFactory()
        other_user = UserFactory()
        datum = ExperimentDataFactory(user=user)
        url = reverse('api_experiments:v0:data-detail', kwargs={'pk': datum.id})
        data = {}

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 401)

        self.client.login(username=user.username, password=UserFactory._DEFAULT_PASSWORD)
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 200)

        self.client.login(username=other_user.username, password=UserFactory._DEFAULT_PASSWORD)
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 404)

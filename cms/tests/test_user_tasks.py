"""
Unit tests for integration of the django-user-tasks app and its REST API.
"""

from __future__ import absolute_import, print_function, unicode_literals

from uuid import uuid4

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import override_settings

from rest_framework.test import APITestCase
from user_tasks.models import UserTaskArtifact, UserTaskStatus
from user_tasks.serializers import ArtifactSerializer, StatusSerializer


# Helper functions for stuff that pylint complains about without disable comments

def _context(response):
    """
    Get a context dictionary for a serializer appropriate for the given response.
    """
    return {'request': response.wsgi_request}  # pylint: disable=no-member


def _data(response):
    """
    Get the serialized data dictionary from the given REST API test response.
    """
    return response.data  # pylint: disable=no-member


@override_settings(BROKER_URL='memory://localhost/')
class TestUserTasks(APITestCase):
    """
    Tests of the django-user-tasks REST API endpoints.

    Detailed tests of the default authorization rules are in the django-user-tasks code.
    These tests just verify that the API is exposed and functioning.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('test_user', 'test@example.com', 'password')
        cls.status = UserTaskStatus.objects.create(
            user=cls.user, task_id=str(uuid4()), task_class='test_rest_api.sample_task', name='SampleTask 2',
            total_steps=5)
        cls.artifact = UserTaskArtifact.objects.create(status=cls.status, text='Lorem ipsum')

    def setUp(self):
        super(TestUserTasks, self).setUp()
        self.status.refresh_from_db()
        self.client.force_authenticate(self.user)  # pylint: disable=no-member

    def test_artifact_detail(self):
        """
        Users should be able to access artifacts for tasks they triggered.
        """
        response = self.client.get(reverse('usertaskartifact-detail', args=[self.artifact.uuid]))
        assert response.status_code == 200
        serializer = ArtifactSerializer(self.artifact, context=_context(response))
        assert _data(response) == serializer.data

    def test_artifact_list(self):
        """
        Users should be able to access a list of their tasks' artifacts.
        """
        response = self.client.get(reverse('usertaskartifact-list'))
        assert response.status_code == 200
        serializer = ArtifactSerializer(self.artifact, context=_context(response))
        assert _data(response)['results'] == [serializer.data]

    def test_status_cancel(self):
        """
        Users should be able to cancel tasks they no longer wish to complete.
        """
        response = self.client.post(reverse('usertaskstatus-cancel', args=[self.status.uuid]))
        assert response.status_code == 200
        self.status.refresh_from_db()
        assert self.status.state == UserTaskStatus.CANCELED

    def test_status_delete(self):
        """
        Users should be able to delete their own task status records when they're done with them.
        """
        response = self.client.delete(reverse('usertaskstatus-detail', args=[self.status.uuid]))
        assert response.status_code == 204
        assert not UserTaskStatus.objects.filter(pk=self.status.id).exists()

    def test_status_detail(self):
        """
        Users should be able to access status records for tasks they triggered.
        """
        response = self.client.get(reverse('usertaskstatus-detail', args=[self.status.uuid]))
        assert response.status_code == 200
        serializer = StatusSerializer(self.status, context=_context(response))
        assert _data(response) == serializer.data

    def test_status_list(self):
        """
        Users should be able to access a list of their tasks' status records.
        """
        response = self.client.get(reverse('usertaskstatus-list'))
        assert response.status_code == 200
        serializer = StatusSerializer([self.status], context=_context(response), many=True)
        assert _data(response)['results'] == serializer.data

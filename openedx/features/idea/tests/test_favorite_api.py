"""
Tests for idea favorite api
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from lms.djangoapps.onboarding.tests.factories import UserFactory
from openedx.features.idea.tests.factories import IdeaFactory


class IdeaFavoriteApiTestCase(TestCase):
    """
    Class contains tests for idea favorite api
    """
    def setUp(self):
        super(IdeaFavoriteApiTestCase, self).setUp()
        self.user = UserFactory()

    def test_toggle_favorite_idea(self):
        idea = IdeaFactory()

        self.client.login(username=self.user.username, password='test')

        response = self.client.post(reverse('mark-favorite-api-view', kwargs=dict(idea_id=idea.id)))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(idea.favorites.filter(pk=self.user.id).exists())

        response = self.client.post(reverse('mark-favorite-api-view', kwargs=dict(idea_id=idea.id)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(idea.favorites.filter(pk=self.user.id).exists())

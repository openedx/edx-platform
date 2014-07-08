"""
Unit tests for change_name view of student.
"""
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test import TestCase

from student.tests.factories import UserFactory
from student.models import UserProfile
import unittest


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestChangeName(TestCase):
    """
    Check the change_name view of student.
    """
    def setUp(self):
        self.student = UserFactory.create(password='test')
        self.client = Client()

    def test_change_name_get_request(self):
        """Get requests are not allowed in this view."""
        change_name_url = reverse('change_name')
        resp = self.client.get(change_name_url)
        self.assertEquals(resp.status_code, 405)

    def test_change_name_post_request(self):
        """Name will be changed when provided with proper data."""
        self.client.login(username=self.student.username, password='test')
        change_name_url = reverse('change_name')
        resp = self.client.post(change_name_url, {
            'new_name': 'waqas',
            'rationale': 'change identity'
        })
        response_data = json.loads(resp.content)
        user = UserProfile.objects.get(user=self.student.id)
        meta = json.loads(user.meta)
        self.assertEquals(user.name, 'waqas')
        self.assertEqual(meta['old_names'][0][1], 'change identity')
        self.assertTrue(response_data['success'])

    def test_change_name_without_name(self):
        """Empty string for name is not allowed in this view."""
        self.client.login(username=self.student.username, password='test')
        change_name_url = reverse('change_name')
        resp = self.client.post(change_name_url, {
            'new_name': '',
            'rationale': 'change identity'
        })
        response_data = json.loads(resp.content)
        self.assertFalse(response_data['success'])

    def test_unauthenticated(self):
        """Unauthenticated user is not allowed to call this view."""
        change_name_url = reverse('change_name')
        resp = self.client.post(change_name_url, {
            'new_name': 'waqas',
            'rationale': 'change identity'
        })
        self.assertEquals(resp.status_code, 404)

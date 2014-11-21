"""
Tests for social
"""
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.factories import UserFactory



class TestSocial(APITestCase):
    """
    Tests for /api/mobile/v0.5/social/...
    """
    def setUp(self):
        pass 

    def test_user_signed_in(self):
        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password='test')
        url = reverse('app-secret')
        response = self.client.get(url)
        self.assertTrue('This is the app secret' in response.data.get('app-secret'))

    def test_user_not_signed_in(self):
        self.user = UserFactory.create()
        url = reverse('app-secret')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        # self.assertTrue(False)
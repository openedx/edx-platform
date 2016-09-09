"""
Tests for AppSecret
"""
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.factories import UserFactory



class TestAppSecret(APITestCase):
    """
    Tests for /api/mobile/v0.5/social/app-secret
    """
    def setUp(self):
        pass 

    def test_user_signed_in_with_correct_app_id(self):
        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password='test')
        url = reverse('app-secret', kwargs={'app_id':'734266930001243'}) 
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("8a982cfdc0922c9fe57bd63edab6b62f" in response.data.get('app-secret'))

    def test_user_signed_in_with_incorrect_app_id(self):
        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password='test')
        url = reverse('app-secret', kwargs={'app_id':'123456'}) 
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("8a982cfdc0922c9fe57bd63edab6b62f" not in response.data.get('app-secret'))

    def test_user_not_signed_in_with_correct_app_id(self):
        self.user = UserFactory.create()
        url = reverse('app-secret', kwargs={'app_id':'734266930001243'}) 
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

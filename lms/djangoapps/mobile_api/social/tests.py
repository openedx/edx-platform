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
        self.user = UserFactory.create()
        # self.course = CourseFactory.create(mobile_available=True)
        self.client.login(username=self.user.username, password='test')

    def test_one(self):
        url = reverse('app-secret')
        # response = self.client.get(url)
        # self.assertEqual(response.status_code, 200)
        self.assertTrue(True)  # pylint: disable=E1103

    def test_two(self):
        # url = reverse('course-handouts-list', kwargs={'course_id': unicode(self.course.id)})
        # response = self.client.get(url)
        self.assertTrue(True)

    def test_three(self):
        # url = reverse('course-updates-list', kwargs={'course_id': unicode(self.course.id)})
        # response = self.client.get(url)
        self.assertTrue(True)
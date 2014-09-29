"""
Tests for course_info
"""
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.factories import UserFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestVideoOutline(ModuleStoreTestCase, APITestCase):
    def setUp(self):
        super(TestVideoOutline, self).setUp()
        self.user = UserFactory.create()
        self.course = CourseFactory.create(mobile_available=True)
        self.client.login(username=self.user.username, password='test')

    def test_about(self):
        url = reverse('course-about-detail', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('overview' in response.data)

    def test_handouts(self):
        url = reverse('course-handouts-list', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_updates(self):
        url = reverse('course-updates-list', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        # TODO: add handouts and updates, somehow

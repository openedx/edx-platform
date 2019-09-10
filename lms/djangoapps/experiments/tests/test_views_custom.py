"""
Tests for experimentation views
"""
from __future__ import absolute_import

from django.urls import reverse
from rest_framework.test import APITestCase

from lms.djangoapps.course_blocks.transformers.tests.helpers import ModuleStoreTestCase
from student.tests.factories import UserFactory

CROSS_DOMAIN_REFERER = 'https://ecommerce.edx.org'


class Rev934Tests(APITestCase, ModuleStoreTestCase):
    def test_logged_in(self):
        """Test mobile app upsell API"""
        url = reverse('api_experiments:rev_934')
        user = UserFactory()

        # Not-logged-in returns 401
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # No-course-id returns show_upsell false
        self.client.login(
            username=user.username,
            password=UserFactory._DEFAULT_PASSWORD,  # pylint: disable=protected-access
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['show_upsell'], False)

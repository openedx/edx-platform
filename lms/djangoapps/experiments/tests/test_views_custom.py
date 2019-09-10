"""
Tests for experimentation views
"""
from __future__ import absolute_import

import unittest

import six.moves.urllib.error  # pylint: disable=import-error
import six.moves.urllib.parse  # pylint: disable=import-error
import six.moves.urllib.request  # pylint: disable=import-error
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch
from rest_framework.test import APITestCase
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag

# from experiments.factories import ExperimentDataFactory, ExperimentKeyValueFactory
from experiments.models import ExperimentData, ExperimentKeyValue
from experiments.serializers import ExperimentDataSerializer
from lms.djangoapps.course_blocks.transformers.tests.helpers import ModuleStoreTestCase
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory

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
        self.client.login(username=user.username, password=UserFactory._DEFAULT_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['show_upsell'], False)



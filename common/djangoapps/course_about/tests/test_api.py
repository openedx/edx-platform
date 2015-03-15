"""
Tests the logical Python API layer of the Course About API.
"""

import ddt
import json
import unittest

from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.conf import settings
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, CourseAboutFactory
from student.tests.factories import UserFactory


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CourseInfoTest(ModuleStoreTestCase, APITestCase):
    """
    Test course information.
    """
    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"

    def setUp(self):
        """ Create a course"""
        super(CourseInfoTest, self).setUp()

        self.course = CourseFactory.create()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def test_get_course_details_from_cache(self):
        kwargs = dict()
        kwargs["course_id"] = self.course.id
        kwargs["course_runtime"] = self.course.runtime
        kwargs["user_id"] = self.user.id
        CourseAboutFactory.create(**kwargs)
        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_data = json.loads(resp.content)
        self.assertIsNotNone(resp_data)

        resp = self.client.get(
            reverse('courseabout', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_data = json.loads(resp.content)
        self.assertIsNotNone(resp_data)

"""
Tests for EmbargoMiddleware
"""

from django.contrib.auth.models import User
from xmodule.modulestore.tests.factories import CourseFactory
from django.test import RequestFactory
from django.test import TestCase
from django.test.utils import override_settings
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from embargo.models import EmbargoConfig
from courseware.views import course_info
from django.test import Client


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class EmbargoMiddlewareTests(TestCase):
    """
    Tests of EmbargoMiddleware
    """
    def setUp(self):
        self.client = Client()
        self.user = User()
        self.client.login(username='fred', password='secret')
        self.course = CourseFactory.create()
        self.course.save()
        self.page = '/courses/' + self.course.id + '/info'
        EmbargoConfig(
            embargoed_countries="CU, IR, SY,SD",
            embargoed_courses=self.course.id,
            changed_by=self.user,
            enabled=True
        ).save()

    def test_countries(self):
        response = self.client.get(self.page, HTTP_X_FORWADED_FOR='0.0.0.0')
        # assert that response.content contains or does not contain embargotext

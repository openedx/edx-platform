"""
These are tests for disabling and enabling student accounts, and for making sure
that students with disabled accounts are unable to access the courseware.
"""
import unittest

from django.http import HttpResponseForbidden
from django.test import RequestFactory, TestCase

from student.tests.factories import UserFactory, UserStandingFactory
from student.middleware import UserStandingMiddleware



class UserStandingTest(TestCase):
    """test suite for user standing view for enabling and disabling accounts"""

    def setUp(self):
        # create users
        self.bad_user = UserFactory.create(
            username='bad_user',
        )
        self.good_user = UserFactory.create(
            username='good_user',
        )

        self.request = RequestFactory().get('foo')

        UserStandingFactory.create(
            disabled=self.bad_user.username,
        )

        self.middleware = UserStandingMiddleware()

    def test_middleware_disabled_user(self):
        self.request.user = self.bad_user
        response = self.middleware.process_request(self.request)
        self.assertIsInstance(response, HttpResponseForbidden)

    def test_middleware_enabled_user(self):
        self.request.user = self.good_user
        self.assertEquals(None, self.middleware.process_request(self.request))

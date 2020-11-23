"""Tests for util.user_utils module."""


import unittest

import six
from django.contrib.auth.models import AnonymousUser

from ..user_utils import SystemUser


class SystemUserTestCase(unittest.TestCase):
    """ Tests for response-related utility functions """
    def setUp(self):
        super(SystemUserTestCase, self).setUp()
        self.sysuser = SystemUser()

    def test_system_user_is_anonymous(self):
        self.assertIsInstance(self.sysuser, AnonymousUser)
        self.assertTrue(self.sysuser.is_anonymous)
        self.assertIsNone(self.sysuser.id)

    def test_system_user_has_custom_unicode_representation(self):
        self.assertNotEqual(six.text_type(self.sysuser), six.text_type(AnonymousUser()))

    def test_system_user_is_not_staff(self):
        self.assertFalse(self.sysuser.is_staff)

    def test_system_user_is_not_superuser(self):
        self.assertFalse(self.sysuser.is_superuser)

"""Tests for util.user_utils module."""


import unittest

from django.contrib.auth.models import AnonymousUser

from ..user_utils import SystemUser


class SystemUserTestCase(unittest.TestCase):
    """ Tests for response-related utility functions """
    def setUp(self):
        super().setUp()
        self.sysuser = SystemUser()

    def test_system_user_is_anonymous(self):
        assert isinstance(self.sysuser, AnonymousUser)
        assert self.sysuser.is_anonymous
        assert self.sysuser.id is None

    def test_system_user_has_custom_unicode_representation(self):
        assert str(self.sysuser) != str(AnonymousUser())

    def test_system_user_is_not_staff(self):
        assert not self.sysuser.is_staff

    def test_system_user_is_not_superuser(self):
        assert not self.sysuser.is_superuser

"""
Tests for the UserService
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import pytest
import six

from xblock.reference.user_service import XBlockUser, UserService


class SingleUserService(UserService):
    """
    This is a dummy user service for testing that always returns a single user.
    """
    def __init__(self, user):
        super(SingleUserService, self).__init__()
        self.user = user

    def get_current_user(self):
        return self.user


def test_dummy_user_service_current_user():
    """
    Tests that get_current_user() works on a dummy user service.
    """
    user = XBlockUser(full_name="tester")
    user_service = SingleUserService(user)
    current_user = user_service.get_current_user()
    assert current_user == user
    assert current_user.full_name == "tester"
    # assert that emails is an Iterable but not a string
    assert isinstance(current_user.emails, collections.Iterable)
    assert not isinstance(current_user.emails, (six.text_type, six.binary_type))
    # assert that opt_attrs is a Mapping
    assert isinstance(current_user.opt_attrs, collections.Mapping)


def test_dummy_user_service_exception():
    """
    Tests NotImplemented error raised by UserService when not instantiated with kwarg get_current_user
    """
    user_service = UserService()
    with pytest.raises(NotImplementedError):
        user_service.get_current_user()

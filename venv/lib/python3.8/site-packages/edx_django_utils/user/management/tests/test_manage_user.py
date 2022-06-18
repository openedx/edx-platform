"""
Unit tests for user_management management commands.
"""


import itertools

import ddt
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.core.management import CommandError, call_command
from django.test import TestCase

from edx_django_utils.user import generate_password

TEST_EMAIL = 'test@example.com'
TEST_USERNAME = 'test-user'
User = get_user_model()


@ddt.ddt
class TestManageUserCommand(TestCase):
    """
    Tests the `manage_user` command.
    """

    def test_user(self):
        """
        Ensures that users are created if they don't exist and reused if they do.
        """
        assert not list(User.objects.all())
        call_command('manage_user', TEST_USERNAME, TEST_EMAIL)
        user = User.objects.get(username=TEST_USERNAME)
        assert user.username == TEST_USERNAME
        assert user.email == TEST_EMAIL

        # check idempotency
        call_command('manage_user', TEST_USERNAME, TEST_EMAIL)
        assert [(TEST_USERNAME, TEST_EMAIL)] == [(u.username, u.email) for u in User.objects.all()]

    def test_remove(self):
        """
        Ensures that users are removed if they exist and exit cleanly otherwise.
        """
        User.objects.create(username=TEST_USERNAME, email=TEST_EMAIL)
        assert [(TEST_USERNAME, TEST_EMAIL)] == [(u.username, u.email) for u in User.objects.all()]
        call_command('manage_user', TEST_USERNAME, TEST_EMAIL, '--remove')
        assert not list(User.objects.all())

        # check idempotency
        call_command('manage_user', TEST_USERNAME, TEST_EMAIL, '--remove')
        assert not list(User.objects.all())

    def test_unusable_password(self):
        """
        Ensure that a user's password is set to an unusable_password.
        """
        user = User.objects.create(username=TEST_USERNAME, email=TEST_EMAIL)
        assert [(TEST_USERNAME, TEST_EMAIL)] == [(u.username, u.email) for u in User.objects.all()]
        user.set_password(generate_password())
        user.save()

        # Run once without passing --unusable-password and make sure the password is usable
        call_command('manage_user', TEST_USERNAME, TEST_EMAIL)
        user = User.objects.get(username=TEST_USERNAME, email=TEST_EMAIL)
        assert user.has_usable_password()

        # Make sure the user now has an unusable_password
        call_command('manage_user', TEST_USERNAME, TEST_EMAIL, '--unusable-password')
        user = User.objects.get(username=TEST_USERNAME, email=TEST_EMAIL)
        assert not user.has_usable_password()

        # check idempotency
        call_command('manage_user', TEST_USERNAME, TEST_EMAIL, '--unusable-password')
        assert not user.has_usable_password()

    def test_initial_password_hash(self):
        """
        Ensure that a user's password hash is set correctly when the user is created,
        and that it isn't touched for existing users.
        """
        initial_hash = make_password('hunter2')

        # Make sure the command aborts if the provided hash isn't a valid Django password hash
        with pytest.raises(CommandError) as exc_context:
            call_command('manage_user', TEST_USERNAME, TEST_EMAIL, '--initial-password-hash', 'invalid_hash')
        assert 'password hash' in str(exc_context.value).lower()

        # Make sure the hash gets set correctly for a new user
        call_command('manage_user', TEST_USERNAME, TEST_EMAIL, '--initial-password-hash', initial_hash)
        user = User.objects.get(username=TEST_USERNAME)
        assert user.password == initial_hash

        # Change the password
        new_hash = make_password('correct horse battery staple')
        user.password = new_hash
        user.save()

        # Verify that calling manage_user again leaves the password untouched
        call_command('manage_user', TEST_USERNAME, TEST_EMAIL, '--initial-password-hash', initial_hash)
        user = User.objects.get(username=TEST_USERNAME)
        assert user.password == new_hash

    def test_wrong_email(self):
        """
        Ensure that the operation is aborted if the username matches an
        existing user account but the supplied email doesn't match.
        """
        User.objects.create(username=TEST_USERNAME, email=TEST_EMAIL)
        with pytest.raises(CommandError) as exc_context:
            call_command('manage_user', TEST_USERNAME, 'other@example.com')
        assert 'email addresses do not match' in str(exc_context.value).lower()
        assert [(TEST_USERNAME, TEST_EMAIL)] == [(u.username, u.email) for u in User.objects.all()]

        # check that removal uses the same check
        with pytest.raises(CommandError) as exc_context:
            call_command('manage_user', TEST_USERNAME, 'other@example.com', '--remove')
        assert 'email addresses do not match' in str(exc_context.value).lower()
        assert [(TEST_USERNAME, TEST_EMAIL)] == [(u.username, u.email) for u in User.objects.all()]

    def test_same_email_varied_case(self):
        """
        Ensure that the operation continues if the username matches an
        existing user account and the supplied email differs only in cases.
        """
        User.objects.create(username=TEST_USERNAME, email=TEST_EMAIL.upper())
        call_command('manage_user', TEST_USERNAME, TEST_EMAIL.lower())
        user = User.objects.get(username=TEST_USERNAME)
        assert user.email == TEST_EMAIL.upper()

    @ddt.data(*itertools.product([(True, True), (True, False), (False, True), (False, False)], repeat=2))
    @ddt.unpack
    def test_bits(self, initial_bits, expected_bits):
        """
        Ensure that the 'staff' and 'superuser' bits are set according to the
        presence / absence of the associated command options, regardless of
        any previous state.
        """
        initial_staff, initial_super = initial_bits
        User.objects.create(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            is_staff=initial_staff,
            is_superuser=initial_super
        )

        expected_staff, expected_super = expected_bits
        args = [opt for bit, opt in ((expected_staff, '--staff'), (expected_super, '--superuser')) if bit]
        call_command('manage_user', TEST_USERNAME, TEST_EMAIL, *args)
        user = User.objects.all().first()
        assert user.is_staff == expected_staff
        assert user.is_superuser == expected_super

    @ddt.data(*itertools.product(('', 'a', 'ab', 'abc'), repeat=2))
    @ddt.unpack
    def test_groups(self, initial_groups, expected_groups):
        """
        Ensures groups assignments are created and deleted idempotently.
        """
        groups = {}
        for group_name in 'abc':
            groups[group_name] = Group.objects.create(name=group_name)

        user = User.objects.create(username=TEST_USERNAME, email=TEST_EMAIL)
        for group_name in initial_groups:
            user.groups.add(groups[group_name])

        call_command('manage_user', TEST_USERNAME, TEST_EMAIL, '-g', *expected_groups)
        actual_groups = [group.name for group in user.groups.all()]
        assert actual_groups == list(expected_groups)

    def test_nonexistent_group(self):
        """
        Ensures the command does not fail if specified groups cannot be found.
        """
        user = User.objects.create(username=TEST_USERNAME, email=TEST_EMAIL)
        groups = {}
        for group_name in 'abc':
            groups[group_name] = Group.objects.create(name=group_name)
            user.groups.add(groups[group_name])

        call_command('manage_user', TEST_USERNAME, TEST_EMAIL, '-g', 'b', 'c', 'd')
        actual_groups = [group.name for group in user.groups.all()]
        assert actual_groups == ['b', 'c']

"""
Unit tests for user_management management commands.
"""


import sys

import ddt
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import CommandError, call_command
from django.test import TestCase

TEST_EMAIL = 'test@example.com'
TEST_GROUP = 'test-group'
TEST_USERNAME = 'test-user'
TEST_DATA = (
    {},
    {
        TEST_GROUP: ['add_group', 'change_group', 'change_group'],
    },
    {
        'other-group': ['add_group', 'change_group', 'change_group'],
    },
)


@ddt.ddt
class TestManageGroupCommand(TestCase):
    """
    Tests the `manage_group` command.
    """

    def set_group_permissions(self, group_permissions):
        """
        Sets up a before-state for groups and permissions in tests, which
        can be checked afterward to ensure that a failed atomic
        operation has not had any side effects.
        """
        content_type = ContentType.objects.get_for_model(Group)
        for group_name, permission_codenames in group_permissions.items():
            group = Group.objects.create(name=group_name)
            for codename in permission_codenames:
                group.permissions.add(
                    Permission.objects.get(content_type=content_type, codename=codename)
                )

    def check_group_permissions(self, group_permissions):
        """
        Checks that the current state of the database matches the specified groups and
        permissions.
        """
        self.check_groups(list(group_permissions.keys()))
        for group_name, permission_codenames in group_permissions.items():
            self.check_permissions(group_name, permission_codenames)

    def check_groups(self, group_names):
        """
        DRY helper.
        """
        self.assertEqual(set(group_names), {g.name for g in Group.objects.all()})

    def check_permissions(self, group_name, permission_codenames):
        """
        DRY helper.
        """
        self.assertEqual(
            set(permission_codenames),
            {p.codename for p in Group.objects.get(name=group_name).permissions.all()}
        )

    @ddt.data(
        *(
            (data, args, exception)
            for data in TEST_DATA
            for args, exception in (
                ((), 'too few arguments' if sys.version_info.major == 2 else 'required: group_name'),  # no group name
                (('x' * 151,), 'invalid group name'),  # invalid group name
                ((TEST_GROUP, 'some-other-group'), 'unrecognized arguments'),  # multiple arguments
                ((TEST_GROUP, '--some-option', 'dummy'), 'unrecognized arguments')  # unexpected option name
            )
        )
    )
    @ddt.unpack
    def test_invalid_input(self, initial_group_permissions, command_args, exception_message):
        """
        Ensures that invalid inputs result in errors with relevant output,
        and that no persistent state is changed.
        """
        self.set_group_permissions(initial_group_permissions)

        with self.assertRaises(CommandError) as exc_context:
            call_command('manage_group', *command_args)
        self.assertIn(exception_message, str(exc_context.exception).lower())
        self.check_group_permissions(initial_group_permissions)

    @ddt.data(*TEST_DATA)
    def test_invalid_permission(self, initial_group_permissions):
        """
        Ensures that a permission that cannot be parsed or resolved results in
        and error and that no persistent state is changed.
        """
        self.set_group_permissions(initial_group_permissions)

        # not parseable
        with self.assertRaises(CommandError) as exc_context:
            call_command('manage_group', TEST_GROUP, '--permissions', 'fail')
        self.assertIn('invalid permission option', str(exc_context.exception).lower())
        self.check_group_permissions(initial_group_permissions)

        # not parseable
        with self.assertRaises(CommandError) as exc_context:
            call_command('manage_group', TEST_GROUP, '--permissions', 'f:a:i:l')
        self.assertIn('invalid permission option', str(exc_context.exception).lower())
        self.check_group_permissions(initial_group_permissions)

        # invalid app label
        with self.assertRaises(CommandError) as exc_context:
            call_command('manage_group', TEST_GROUP, '--permissions', 'nonexistent-label:dummy-model:dummy-perm')
        self.assertIn('no installed app', str(exc_context.exception).lower())
        self.assertIn('nonexistent-label', str(exc_context.exception).lower())
        self.check_group_permissions(initial_group_permissions)

        # invalid model name
        with self.assertRaises(CommandError) as exc_context:
            call_command('manage_group', TEST_GROUP, '--permissions', 'auth:nonexistent-model:dummy-perm')
        self.assertIn('nonexistent-model', str(exc_context.exception).lower())
        self.check_group_permissions(initial_group_permissions)

        # invalid model name
        with self.assertRaises(CommandError) as exc_context:
            call_command('manage_group', TEST_GROUP, '--permissions', 'auth:Group:nonexistent-perm')
        self.assertIn('invalid permission codename', str(exc_context.exception).lower())
        self.assertIn('nonexistent-perm', str(exc_context.exception).lower())
        self.check_group_permissions(initial_group_permissions)

    def test_group(self):
        """
        Ensures that groups are created if they don't exist and reused if they do.
        """
        self.check_groups([])
        call_command('manage_group', TEST_GROUP)
        self.check_groups([TEST_GROUP])

        # check idempotency
        call_command('manage_group', TEST_GROUP)
        self.check_groups([TEST_GROUP])

    def test_group_remove(self):
        """
        Ensures that groups are removed if they exist and we exit cleanly otherwise.
        """
        self.set_group_permissions({TEST_GROUP: ['add_group']})
        self.check_groups([TEST_GROUP])
        call_command('manage_group', TEST_GROUP, '--remove')
        self.check_groups([])

        # check idempotency
        call_command('manage_group', TEST_GROUP, '--remove')
        self.check_groups([])

    def test_permissions(self):
        """
        Ensures that permissions are set on the group as specified.
        """
        self.check_groups([])
        call_command('manage_group', TEST_GROUP, '--permissions', 'auth:Group:add_group')
        self.check_groups([TEST_GROUP])
        self.check_permissions(TEST_GROUP, ['add_group'])

        # check idempotency
        call_command('manage_group', TEST_GROUP, '--permissions', 'auth:Group:add_group')
        self.check_groups([TEST_GROUP])
        self.check_permissions(TEST_GROUP, ['add_group'])

        # check adding a permission
        call_command('manage_group', TEST_GROUP, '--permissions', 'auth:Group:add_group', 'auth:Group:change_group')
        self.check_groups([TEST_GROUP])
        self.check_permissions(TEST_GROUP, ['add_group', 'change_group'])

        # check removing a permission
        call_command('manage_group', TEST_GROUP, '--permissions', 'auth:Group:change_group')
        self.check_groups([TEST_GROUP])
        self.check_permissions(TEST_GROUP, ['change_group'])

        # check removing all permissions
        call_command('manage_group', TEST_GROUP)
        self.check_groups([TEST_GROUP])
        self.check_permissions(TEST_GROUP, [])

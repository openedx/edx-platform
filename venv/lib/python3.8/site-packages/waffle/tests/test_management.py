import io

from django.core.management import call_command, CommandError
from django.contrib.auth.models import Group, User

from waffle import get_waffle_flag_model
from waffle.models import Sample, Switch
from waffle.tests.base import TestCase


class WaffleFlagManagementCommandTests(TestCase):
    def test_create(self):
        """ The command should create a new flag. """
        name = 'test'
        percent = 20
        Group.objects.create(name='waffle_group')
        call_command('waffle_flag', name, percent=percent,
                     superusers=True, staff=True, authenticated=True,
                     rollout=True, create=True, group=['waffle_group'])

        flag = get_waffle_flag_model().objects.get(name=name)
        self.assertEqual(flag.percent, percent)
        self.assertIsNone(flag.everyone)
        self.assertTrue(flag.superusers)
        self.assertTrue(flag.staff)
        self.assertTrue(flag.authenticated)
        self.assertTrue(flag.rollout)
        self.assertEqual(list(flag.groups.values_list('name', flat=True)),
                         ['waffle_group'])

    def test_not_create(self):
        """ The command shouldn't create a new flag if the create flag is
        not set.
        """
        name = 'test'
        with self.assertRaisesRegex(CommandError, 'This flag does not exist.'):
            call_command('waffle_flag', name, everyone=True, percent=20,
                         superusers=True, staff=True, authenticated=True,
                         rollout=True)
        self.assertFalse(get_waffle_flag_model().objects.filter(name=name).exists())

    def test_update(self):
        """ The command should update an existing flag. """
        name = 'test'
        flag = get_waffle_flag_model().objects.create(name=name)
        self.assertIsNone(flag.percent)
        self.assertIsNone(flag.everyone)
        self.assertTrue(flag.superusers)
        self.assertFalse(flag.staff)
        self.assertFalse(flag.authenticated)
        self.assertFalse(flag.rollout)

        percent = 30
        call_command('waffle_flag', name, percent=percent,
                     superusers=False, staff=True, authenticated=True,
                     rollout=True)

        flag.refresh_from_db()
        self.assertEqual(flag.percent, percent)
        self.assertIsNone(flag.everyone)
        self.assertFalse(flag.superusers)
        self.assertTrue(flag.staff)
        self.assertTrue(flag.authenticated)
        self.assertTrue(flag.rollout)

    def test_update_activate_everyone(self):
        """ The command should update everyone field to True """
        name = 'test'
        flag = get_waffle_flag_model().objects.create(name=name)
        self.assertIsNone(flag.percent)
        self.assertIsNone(flag.everyone)
        self.assertTrue(flag.superusers)
        self.assertFalse(flag.staff)
        self.assertFalse(flag.authenticated)
        self.assertFalse(flag.rollout)

        percent = 30
        call_command('waffle_flag', name, everyone=True, percent=percent,
                     superusers=False, staff=True, authenticated=True,
                     rollout=True)

        flag.refresh_from_db()
        self.assertEqual(flag.percent, percent)
        self.assertTrue(flag.everyone)
        self.assertFalse(flag.superusers)
        self.assertTrue(flag.staff)
        self.assertTrue(flag.authenticated)
        self.assertTrue(flag.rollout)

    def test_update_deactivate_everyone(self):
        """ The command should update everyone field to False"""
        name = 'test'
        flag = get_waffle_flag_model().objects.create(name=name)
        self.assertIsNone(flag.percent)
        self.assertIsNone(flag.everyone)
        self.assertTrue(flag.superusers)
        self.assertFalse(flag.staff)
        self.assertFalse(flag.authenticated)
        self.assertFalse(flag.rollout)

        percent = 30
        call_command('waffle_flag', name, everyone=False, percent=percent,
                     superusers=False, staff=True, authenticated=True,
                     rollout=True)

        flag.refresh_from_db()
        self.assertEqual(flag.percent, percent)
        self.assertFalse(flag.everyone)
        self.assertFalse(flag.superusers)
        self.assertTrue(flag.staff)
        self.assertTrue(flag.authenticated)
        self.assertTrue(flag.rollout)

    def test_list(self):
        """ The command should list all flags."""
        stdout = io.StringIO()
        get_waffle_flag_model().objects.create(name='test')

        call_command('waffle_flag', list_flags=True, stdout=stdout)
        expected = 'Flags:\nNAME: test\nSUPERUSERS: True\nEVERYONE: None\n' \
                   'AUTHENTICATED: False\nPERCENT: None\nTESTING: False\n' \
                   'ROLLOUT: False\nSTAFF: False\nGROUPS: []\nUSERS: []'
        actual = stdout.getvalue().strip()
        self.assertEqual(actual, expected)

    def test_group_append(self):
        """ The command should append a group to a flag."""
        original_group = Group.objects.create(name='waffle_group')
        Group.objects.create(name='append_group')
        flag = get_waffle_flag_model().objects.create(name='test')
        flag.groups.add(original_group)
        flag.refresh_from_db()

        self.assertEqual(list(flag.groups.values_list('name', flat=True)),
                         ['waffle_group'])

        call_command('waffle_flag', 'test', group=['append_group'],
                     append=True)

        flag.refresh_from_db()
        self.assertEqual(list(flag.groups.values_list('name', flat=True)),
                         ['waffle_group', 'append_group'])
        self.assertIsNone(flag.everyone)

    def test_user(self):
        """ The command should replace a user to a flag."""
        original_user = User.objects.create_user('waffle_test')
        User.objects.create_user('add_user')
        flag = get_waffle_flag_model().objects.create(name='test')
        flag.users.add(original_user)
        flag.refresh_from_db()

        self.assertEqual(list(flag.users.values_list('username', flat=True)),
                         ['waffle_test'])

        call_command('waffle_flag', 'test', user=['add_user'])

        flag.refresh_from_db()
        self.assertEqual(list(flag.users.values_list('username', flat=True)),
                         ['add_user'])
        self.assertIsNone(flag.everyone)

    def test_user_append(self):
        """ The command should append a user to a flag."""
        original_user = User.objects.create_user('waffle_test')
        User.objects.create_user('append_user')
        User.objects.create_user('append_user_email', email='test@example.com')
        flag = get_waffle_flag_model().objects.create(name='test')
        flag.users.add(original_user)
        flag.refresh_from_db()

        self.assertEqual(list(flag.users.values_list('username', flat=True)),
                         ['waffle_test'])

        call_command('waffle_flag', 'test', user=['append_user'],
                     append=True)

        flag.refresh_from_db()
        self.assertEqual(list(flag.users.values_list('username', flat=True)),
                         ['waffle_test', 'append_user'])
        self.assertIsNone(flag.everyone)

        call_command('waffle_flag', 'test', user=['test@example.com'],
                     append=True)

        flag.refresh_from_db()
        self.assertEqual(list(flag.users.values_list('username', flat=True)),
                         ['waffle_test', 'append_user', 'append_user_email'])
        self.assertIsNone(flag.everyone)


class WaffleSampleManagementCommandTests(TestCase):
    def test_create(self):
        """ The command should create a new sample. """
        name = 'test'
        percent = 20
        call_command('waffle_sample', name, str(percent), create=True)

        sample = Sample.objects.get(name=name)
        self.assertEqual(sample.percent, percent)

    def test_not_create(self):
        """ The command shouldn't create a new sample if the create flag is
        not set.
        """
        name = 'test'
        with self.assertRaisesRegex(CommandError, 'This sample does not exist'):
            call_command('waffle_sample', name, '20')
        self.assertFalse(Sample.objects.filter(name=name).exists())

    def test_update(self):
        """ The command should update an existing sample. """
        name = 'test'
        sample = Sample.objects.create(name=name, percent=0)
        self.assertEqual(sample.percent, 0)

        percent = 50
        call_command('waffle_sample', name, str(percent))

        sample.refresh_from_db()
        self.assertEqual(sample.percent, percent)

    def test_list(self):
        """ The command should list all samples."""
        stdout = io.StringIO()
        Sample.objects.create(name='test', percent=34)

        call_command('waffle_sample', list_samples=True, stdout=stdout)
        expected = 'Samples:\ntest: 34.0%'
        actual = stdout.getvalue().strip()
        self.assertEqual(actual, expected)


class WaffleSwitchManagementCommandTests(TestCase):
    def test_create(self):
        """ The command should create a new switch. """
        name = 'test'

        call_command('waffle_switch', name, 'on', create=True)
        switch = Switch.objects.get(name=name, active=True)
        switch.delete()

        call_command('waffle_switch', name, 'off', create=True)
        Switch.objects.get(name=name, active=False)

    def test_not_create(self):
        """ The command shouldn't create a new switch if the create flag is
        not set.
        """
        name = 'test'
        with self.assertRaisesRegex(CommandError, 'This switch does not exist.'):
            call_command('waffle_switch', name, 'on')
        self.assertFalse(Switch.objects.filter(name=name).exists())

    def test_update(self):
        """ The command should update an existing switch. """
        name = 'test'
        switch = Switch.objects.create(name=name, active=True)

        call_command('waffle_switch', name, 'off')
        switch.refresh_from_db()
        self.assertFalse(switch.active)

        call_command('waffle_switch', name, 'on')
        switch.refresh_from_db()
        self.assertTrue(switch.active)

    def test_list(self):
        """ The command should list all switches."""
        stdout = io.StringIO()
        Switch.objects.create(name='switch1', active=True)
        Switch.objects.create(name='switch2', active=False)

        call_command('waffle_switch', list_switches=True, stdout=stdout)
        expected = 'Switches:\nswitch1: on\nswitch2: off'
        actual = stdout.getvalue().strip()
        self.assertEqual(actual, expected)


class WaffleDeleteManagementCommandTests(TestCase):
    def test_delete_flag(self):
        """ The command should delete a flag. """
        name = 'test_flag'
        get_waffle_flag_model().objects.create(name=name)

        call_command('waffle_delete', flag_names=[name])
        self.assertEqual(get_waffle_flag_model().objects.count(), 0)

    def test_delete_swtich(self):
        """ The command should delete a switch. """
        name = 'test_switch'
        Switch.objects.create(name=name)

        call_command('waffle_delete', switch_names=[name])
        self.assertEqual(Switch.objects.count(), 0)

    def test_delete_sample(self):
        """ The command should delete a sample. """
        name = 'test_sample'
        Sample.objects.create(name=name, percent=0)

        call_command('waffle_delete', sample_names=[name])
        self.assertEqual(Sample.objects.count(), 0)

    def test_delete_mix_of_types(self):
        """ The command should delete different types of records. """
        name = 'test'
        get_waffle_flag_model().objects.create(name=name)
        Switch.objects.create(name=name)
        Sample.objects.create(name=name, percent=0)
        call_command('waffle_delete', switch_names=[name], flag_names=[name],
                     sample_names=[name])

        self.assertEqual(get_waffle_flag_model().objects.count(), 0)
        self.assertEqual(Switch.objects.count(), 0)
        self.assertEqual(Sample.objects.count(), 0)

    def test_delete_some_but_not_all_records(self):
        """ The command should delete specified records, but leave records
        not specified alone. """
        flag_1 = 'test_flag_1'
        flag_2 = 'test_flag_2'
        get_waffle_flag_model().objects.create(name=flag_1)
        get_waffle_flag_model().objects.create(name=flag_2)

        call_command('waffle_delete', flag_names=[flag_1])
        self.assertTrue(get_waffle_flag_model().objects.filter(name=flag_2).exists())

try:
    import mock
except ImportError:
    import unittest.mock as mock
import unittest

import django
from django.contrib.admin.models import LogEntry, CHANGE, DELETION
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from waffle import get_waffle_flag_model
from waffle.admin import (FlagAdmin, SwitchAdmin, InformativeManyToManyRawIdWidget, enable_for_all,
                          disable_for_all, delete_individually, enable_switches, disable_switches)
from waffle.models import Switch
from waffle.tests.base import TestCase


django_version = tuple(int(d) for d in django.get_version().split("."))


class FakeSuperUser:
    def has_perm(self, perm):
        return True


class FakeRequest:
    def __init__(self):
        self.GET = {}
        self.user = get_user_model().objects.create(username="test1")


Flag = get_waffle_flag_model()


skip_if_admin_permissions_not_available = \
    unittest.skipIf(django_version < (2, 1, 0), "Feature not available")


class FlagAdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.flag_admin = FlagAdmin(Flag, self.site)

    def test_informative_widget(self):
        request = mock.Mock()
        request.has_perm = lambda self, perm: True
        form = self.flag_admin.get_form(request)()
        user_widget = form.fields["users"].widget

        self.assertIsInstance(user_widget, InformativeManyToManyRawIdWidget)
        user1 = get_user_model().objects.create(username="test1")
        user2 = get_user_model().objects.create(username="test2")
        self.assertIn("(test1, test2)",
                      user_widget.render("users", [user1.pk, user2.pk]))

    def test_enable_for_all(self):
        f1 = Flag.objects.create(name="flag1", everyone=False)

        request = FakeRequest()
        enable_for_all(None, request, Flag.objects.all())

        f1.refresh_from_db()
        self.assertTrue(f1.everyone)
        log_entry = LogEntry.objects.get(user=request.user)
        self.assertEqual(log_entry.action_flag, CHANGE)
        self.assertEqual(log_entry.object_repr, "flag1 on")

    def test_disable_for_all(self):
        f1 = Flag.objects.create(name="flag1", everyone=True)

        request = FakeRequest()
        disable_for_all(None, request, Flag.objects.all())

        f1.refresh_from_db()
        self.assertFalse(f1.everyone)
        log_entry = LogEntry.objects.get(user=request.user)
        self.assertEqual(log_entry.action_flag, CHANGE)
        self.assertEqual(log_entry.object_repr, "flag1 off")

    def test_delete_individually(self):
        Flag.objects.create(name="flag1", everyone=True)

        request = FakeRequest()
        delete_individually(None, request, Flag.objects.all())

        self.assertIsNone(Flag.objects.first())
        log_entry = LogEntry.objects.get(user=request.user)
        self.assertEqual(log_entry.action_flag, DELETION)

    @skip_if_admin_permissions_not_available
    def test_flag_no_actions_without_permissions(self):
        request = FakeRequest()
        actions = self.flag_admin.get_actions(request)

        self.assertEqual(actions.keys(), set())

    @skip_if_admin_permissions_not_available
    def test_flag_action_change(self):
        request = FakeRequest()
        request.user.user_permissions.add(Permission.objects.get(codename="change_flag"))
        actions = self.flag_admin.get_actions(request)

        self.assertEqual(actions.keys(), {"enable_for_all", "disable_for_all"})

    @skip_if_admin_permissions_not_available
    def test_flag_action_delete(self):
        request = FakeRequest()
        request.user.user_permissions.add(Permission.objects.get(codename="delete_flag"))
        actions = self.flag_admin.get_actions(request)

        self.assertEqual(actions.keys(), {"delete_individually"})


class SwitchAdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.switch_admin = SwitchAdmin(Switch, self.site)

    def test_enable_switches(self):
        s1 = Switch.objects.create(name="switch1", active=False)

        request = FakeRequest()
        enable_switches(None, request, Switch.objects.all())

        s1.refresh_from_db()
        self.assertTrue(s1.active)
        log_entry = LogEntry.objects.get(user=request.user)
        self.assertEqual(log_entry.action_flag, CHANGE)
        self.assertEqual(log_entry.object_repr, "switch1 on")

    def test_disable_switches(self):
        s1 = Switch.objects.create(name="switch1", active=True)

        request = FakeRequest()
        disable_switches(None, request, Switch.objects.all())

        s1.refresh_from_db()
        self.assertFalse(s1.active)
        log_entry = LogEntry.objects.get(user=request.user)
        self.assertEqual(log_entry.action_flag, CHANGE)
        self.assertEqual(log_entry.object_repr, "switch1 off")

    @skip_if_admin_permissions_not_available
    def test_switch_no_actions_without_permissions(self):
        request = FakeRequest()
        actions = self.switch_admin.get_actions(request)

        self.assertEqual(actions.keys(), set())

    @skip_if_admin_permissions_not_available
    def test_switch_action_change(self):
        request = FakeRequest()
        request.user.user_permissions.add(Permission.objects.get(codename="change_switch"))
        actions = self.switch_admin.get_actions(request)

        self.assertEqual(actions.keys(), {"enable_switches", "disable_switches"})

    @skip_if_admin_permissions_not_available
    def test_switch_action_delete(self):
        request = FakeRequest()
        request.user.user_permissions.add(Permission.objects.get(codename="delete_switch"))
        actions = self.switch_admin.get_actions(request)

        self.assertEqual(actions.keys(), {"delete_individually"})

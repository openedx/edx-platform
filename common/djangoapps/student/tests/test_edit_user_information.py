"""
Unit tests for edit_user_profile view of student.
"""

import json
import unittest
from mock import patch

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.translation import ugettext as _

from student.tests.factories import UserFactory, UserProfileFactory
from student.models import UserProfile


class lms_patch_dict(object):
    """
    Tiny utility to patch dict settings only when we are running the lms tests.
    This is necessary because e.g: the REGISTRATION_EXTRA_FIELDS does not exist
    in cms settings. Overriding settings does not work, as it does not modify
    the currently imported settings object. If you wish to try an alternate
    solution, try to run this test case with both the lms and cms service.
    """

    def __init__(self, setting, in_dict):
        self.setting = setting
        self.in_dict = in_dict

    def __call__(self, func):
        if settings.ROOT_URLCONF == 'lms.urls':
            return patch.dict(getattr(settings, self.setting), self.in_dict)(func)
        else:
            return func


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestEditUserInformation(TestCase):

    def setUp(self):
        self.student = UserFactory.create(
            first_name='john',
            last_name='doe',
            password='test',
        )
        self.student.profile = UserProfileFactory.create(
            user=self.student,
        )
        self.client.login(username=self.student.username, password='test')

    def set_field(self, field, value):
        setattr(self.student.profile, field, value)
        self.student.profile.save()

    def post(self, **data):
        url = reverse('edit_user_information')
        return self.client.post(url, data=data)

    @lms_patch_dict("REGISTRATION_EXTRA_FIELDS", {'city': 'optional'})
    def test_dont_change_anything(self):
        self.set_field("city", "Smallville")
        response = self.post()

        self.assertEqual(200, response.status_code)
        self.assertTrue(json.loads(response.content)["success"])
        self.assertEqual('Smallville', UserProfile.objects.get(user=self.student).city)

    @lms_patch_dict("REGISTRATION_EXTRA_FIELDS", {'city': 'optional'})
    def test_change_optional_field(self):
        self.set_field("city", "Smallville")
        self.post(city='Madranque')
        self.assertEqual('Madranque', UserProfile.objects.get(user=self.student).city)

    @lms_patch_dict("REGISTRATION_EXTRA_FIELDS", {'city': 'hidden'})
    def test_hidden_field_is_skipped(self):
        self.set_field("city", "Smallville")
        response = self.post(city='Madranque')
        response_result = json.loads(response.content)

        self.assertFalse(response_result["success"])
        self.assertIn("errors", response_result)
        self.assertIn(_("City"), response_result["errors"])
        self.assertEqual(1, len(response_result["errors"][_("City")]))
        self.assertEqual(_("This field is not editable"), response_result["errors"][_("City")][0])
        self.assertEqual("Smallville", UserProfile.objects.get(user=self.student).city)

    @lms_patch_dict("REGISTRATION_EXTRA_FIELDS", {'country': 'required'})
    def test_required_field_must_be_set(self):
        self.set_field('country', None)
        response = self.post()
        response_result = json.loads(response.content)
        self.assertEqual(1, len(response_result["errors"][_('Country')]))

    def test_logged_out_user_has_no_access(self):
        self.client.logout()
        response = self.post()
        self.assertEqual(302, response.status_code)

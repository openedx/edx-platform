# -*- coding: utf-8 -*-
"""
Test that various events are fired for models in the student app.
"""
from django.test import TestCase

from student.tests.factories import UserFactory
from student.tests.tests import UserProfileEventTestMixin


class TestUserProfileEvents(UserProfileEventTestMixin, TestCase):
    """
    Test that we emit field change events when UserProfile models are changed.
    """
    def setUp(self):
        super(TestUserProfileEvents, self).setUp()
        self.user = UserFactory.create()
        self.profile = self.user.profile
        self.reset_tracker()

    def test_change_one_field(self):
        """
        Verify that we emit an event when a single field changes on the user
        profile.
        """
        self.profile.year_of_birth = 1900
        self.profile.save()
        self.assert_profile_event_emitted(setting='year_of_birth', old=None, new=self.profile.year_of_birth)

    def test_change_many_fields(self):
        """
        Verify that we emit one event per field when many fields change on the
        user profile in one transaction.
        """
        self.profile.gender = u'o'
        self.profile.bio = 'test bio'
        self.profile.save()
        self.assert_profile_event_emitted(setting='bio', old=None, new=self.profile.bio)
        self.assert_profile_event_emitted(setting='gender', old=u'm', new=u'o')

    def test_unicode(self):
        """
        Verify that the events we emit can handle unicode characters.
        """
        old_name = self.profile.name
        self.profile.name = u'Dånîél'
        self.profile.save()
        self.assert_profile_event_emitted(setting='name', old=old_name, new=self.profile.name)

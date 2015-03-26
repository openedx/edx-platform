# -*- coding: utf-8 -*-
""" Tests for student profile views. """

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from util.testing import UrlResetMixin
from student.tests.factories import UserFactory

from student_profile.views import learner_profile_context


class LearnerProfileViewTest(UrlResetMixin, TestCase):
    """ Tests for the student profile view. """

    USERNAME = "username"
    PASSWORD = "password"
    CONTEXT_DATA = [
        'default_public_account_fields',
        'accounts_api_url',
        'preferences_api_url',
        'account_settings_page_url',
        'has_preferences_access',
        'own_profile',
        'country_options',
        'language_options',
    ]

    def setUp(self):
        super(LearnerProfileViewTest, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def test_context(self):
        """
        Verify learner profile page context data.
        """
        context = learner_profile_context(self.user.username, self.USERNAME, self.user.is_staff)

        self.assertEqual(
            context['data']['default_public_account_fields'],
            settings.ACCOUNT_VISIBILITY_CONFIGURATION['public_fields']
        )

        self.assertEqual(
            context['data']['accounts_api_url'],
            reverse("accounts_api", kwargs={'username': self.user.username})
        )

        self.assertEqual(
            context['data']['preferences_api_url'],
            reverse('preferences_api', kwargs={'username': self.user.username})
        )

        self.assertEqual(context['data']['account_settings_page_url'], reverse('account_settings'))

        for attribute in self.CONTEXT_DATA:
            self.assertIn(attribute, context['data'])

    def test_view(self):
        """
        Verify learner profile page view.
        """
        profile_path = reverse('learner_profile', kwargs={'username': self.USERNAME})
        response = self.client.get(path=profile_path)

        for attribute in self.CONTEXT_DATA:
            self.assertIn(attribute, response.content)

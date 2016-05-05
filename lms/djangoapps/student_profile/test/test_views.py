# -*- coding: utf-8 -*-
""" Tests for student profile views. """

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory

from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from student.tests.factories import UserFactory
from student_profile.views import learner_profile_context
from util.testing import UrlResetMixin


class LearnerProfileViewTest(UrlResetMixin, TestCase, ProgramsApiConfigMixin):
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
        'account_settings_data',
        'preferences_data',
    ]

    def setUp(self):
        super(LearnerProfileViewTest, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def test_context(self):
        """
        Verify learner profile page context data.
        """
        request = RequestFactory().get('/url')
        request.user = self.user

        context = learner_profile_context(request, self.USERNAME, self.user.is_staff)

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

        self.assertEqual(
            context['data']['profile_image_upload_url'],
            reverse("profile_image_upload", kwargs={'username': self.user.username})
        )

        self.assertEqual(
            context['data']['profile_image_remove_url'],
            reverse('profile_image_remove', kwargs={'username': self.user.username})
        )

        self.assertEqual(
            context['data']['profile_image_max_bytes'],
            settings.PROFILE_IMAGE_MAX_BYTES
        )

        self.assertEqual(
            context['data']['profile_image_min_bytes'],
            settings.PROFILE_IMAGE_MIN_BYTES
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

    def test_undefined_profile_page(self):
        """
        Verify that a 404 is returned for a non-existent profile page.
        """
        profile_path = reverse('learner_profile', kwargs={'username': "no_such_user"})
        response = self.client.get(path=profile_path)
        self.assertEqual(404, response.status_code)

    def test_header_with_programs_listing_enabled(self):
        """
        Verify that tabs header will be shown while program listing is enabled.
        """
        self.create_programs_config(program_listing_enabled=True)
        profile_path = reverse('learner_profile', kwargs={'username': self.USERNAME})
        response = self.client.get(path=profile_path)

        self.assertContains(response, '<li class="tab-nav-item">')

    def test_header_with_programs_listing_disabled(self):
        """
        Verify that nav header will be shown while program listing is disabled.
        """
        self.create_programs_config(program_listing_enabled=False)
        profile_path = reverse('learner_profile', kwargs={'username': self.USERNAME})
        response = self.client.get(path=profile_path)

        self.assertContains(response, '<li class="item nav-global-01">')

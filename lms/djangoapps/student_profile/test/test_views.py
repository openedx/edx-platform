# -*- coding: utf-8 -*-
""" Tests for student profile views. """

from django.core.urlresolvers import reverse
from django.test import TestCase

from util.testing import UrlResetMixin
from openedx.core.djangoapps.user_api.api import account as account_api


class LearnerProfileTest(UrlResetMixin, TestCase):
    """ Tests for the student profile views. """

    USERNAME = "sour_heart"
    PASSWORD = u"forgotten"
    EMAIL = u"sour_heart@useless.com"

    def setUp(self):
        super(LearnerProfileTest, self).setUp()

        # Create/activate a new account
        activation_key = account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        account_api.activate_account(activation_key)

        # Login
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result)

    def test_learner_profile_view(self):
        """
        Verify that learner profile view is rendered with correct data.
        """
        profile_path = reverse('learner_profile', kwargs={'username': self.USERNAME})
        response = self.client.get(path=profile_path)

        self.assertTrue('href="{}"'.format(profile_path) in response.content)
        self.assertTrue('class="learner-profile-container"' in response.content)
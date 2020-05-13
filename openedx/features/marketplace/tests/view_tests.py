# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.urls import reverse

from lms.djangoapps.onboarding.models import Organization
from lms.djangoapps.onboarding.tests.factories import UserFactory
from openedx.core.djangolib.testing.philu_utils import configure_philu_theme


class MarketplaceViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super(MarketplaceViewTests, cls).setUpClass()
        configure_philu_theme()

    def setUp(self):
        super(MarketplaceViewTests, self).setUp()
        self.user = UserFactory()
        self.organization, _created = Organization.objects.get_or_create(label='Arbisoft')
        self.user.extended_profile.organization = self.organization
        self.user.extended_profile.save()
        self.payload = {
            'organization': self.organization.id,
            'country': 'PK',
            'city': 'Lahore',
            'organization_mission': 'mission statement',
            'organization_sector': 'health-and-well-being',
            'organizational_problems': 'remote-working-tools',
            'description': 'Brief Description of Challenges',
            'approach_to_address': 'How has your organization already tried to address these challenges?',
            'resources_currently_using': 'What tools or resources are you currently using?',
            'user_services': 'delivery-services',
            'video_link': 'http://link-to-video.com',
            'user': self.user.id
        }

    def test_get_marketplace_listing_page(self):
        response = self.client.get(reverse('marketplace-listing'))
        self.assertEqual(response.status_code, 200)

    def test_get_marketplace_make_request_page(self):
        self.client.login(username=self.user.username, password='test')
        response = self.client.get(reverse('marketplace-make-request'), follow=True)
        self.assertEquals(response.status_code, 200)

    def test_marketplace_request_form(self):
        self.client.login(username=self.user.username, password='test')
        response = self.client.post(reverse('marketplace-make-request'), self.payload, follow=True)
        self.assertRedirects(response, reverse('marketplace-listing'))

    def test_get_marketplace_details_page(self):
        self.client.login(username=self.user.username, password='test')
        self.client.post(reverse('marketplace-make-request'), self.payload, follow=True)
        response = self.client.get(reverse('marketplace-details', kwargs=dict(pk=1)))
        self.assertEqual(response.status_code, 200)

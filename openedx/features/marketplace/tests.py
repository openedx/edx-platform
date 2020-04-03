# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.sites.models import Site
from django.test import TestCase

from django.urls import reverse

from openedx.core.djangoapps.theming.models import SiteTheme


class MarketplaceViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super(MarketplaceViewTests, cls).setUpClass()
        site = Site(domain='testserver', name='test')
        site.save()
        theme = SiteTheme(site=site, theme_dir_name='philu')
        theme.save()

    def test_get_marketplace_listing_page(self):
        response = self.client.get(reverse('marketplace-listing'))
        self.assertEqual(response.status_code, 200)

    def test_get_marketplace_make_request_page(self):
        response = self.client.get(reverse('marketplace-make-request'))
        self.assertEqual(response.status_code, 200)

    def test_get_marketplace_details_page(self):
        response = self.client.get(reverse('marketplace-details', kwargs=dict(pk=1)))
        self.assertEqual(response.status_code, 200)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.sites.models import Site
from django.test import TestCase
from django.urls import reverse

from openedx.core.djangoapps.theming.models import SiteTheme


class ChallengeViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super(ChallengeViewTests, cls).setUpClass()
        site = Site(domain='testserver', name='test')
        site.save()
        theme = SiteTheme(site=site, theme_dir_name='philu')
        theme.save()

    def test_get_idea_challange_page(self):
        response = self.client.get(reverse('challenge-landing'))
        self.assertEqual(response.status_code, 200)

    def test_get_idea_listing_page(self):
        response = self.client.get(reverse('idea-listing'))
        self.assertEqual(response.status_code, 200)

    def test_get_idea_create_page(self):
        response = self.client.get(reverse('idea-create'))
        self.assertEqual(response.status_code, 200)

    def test_get_idea_details_page(self):
        response = self.client.get(reverse('idea-details', kwargs=dict(pk=1)))
        self.assertEqual(response.status_code, 200)

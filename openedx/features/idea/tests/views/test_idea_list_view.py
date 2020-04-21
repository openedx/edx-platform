from django.contrib.sites.models import Site
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from openedx.core.djangoapps.theming.models import SiteTheme
from openedx.features.idea.views import IdeaListingView


class IdeaListingViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super(IdeaListingViewTest, cls).setUpClass()
        site = Site(domain='testserver', name='test')
        site.save()
        theme = SiteTheme(site=site, theme_dir_name='philu')
        theme.save()

    def test_idea_list_view(self):
        response = self.client.get(reverse('idea-listing'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(IdeaListingView.paginate_by, 9)
        self.assertEqual(IdeaListingView.ordering, ['-created'])

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from openedx.core.djangolib.testing.philu_utils import configure_philu_theme
from openedx.features.idea.views import IdeaListingView


class IdeaListingViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super(IdeaListingViewTest, cls).setUpClass()
        configure_philu_theme()

    def test_idea_list_view(self):
        response = self.client.get(reverse('idea-listing'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(IdeaListingView.paginate_by, 9)
        self.assertEqual(IdeaListingView.ordering, ['-created'])

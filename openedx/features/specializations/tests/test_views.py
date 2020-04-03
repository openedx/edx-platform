from mock import Mock, patch

from django.contrib.sites.models import Site
from django.test import Client, TestCase
from django.urls import reverse

from common.lib.discovery_client.client import DiscoveryClient
from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.theming.models import SiteTheme

from mock_get_program_helpers import *


def intercept_renderer(path, context):
    """
    Intercept calls to `render_to_response` and attach the context dict to the
    response for examination in unit tests.
    """
    # I think Django already does this for you in their TestClient, except
    # we're bypassing that by using edxmako.  Probably edxmako should be
    # integrated better with Django's rendering and event system.
    response = render_to_response(path, context)
    response.mako_context = context
    response.mako_template = path
    return response

class AboutViewTest(TestCase):

    def setUp(self):
        super(AboutViewTest, self).setUp()
        self.client = Client()
        self.path = reverse('specialization_about', kwargs={
            'specialization_uuid': 'eb228773-a9a5-48cf-bb0e-94725d5aa4f1'
        })

    @classmethod
    def setUpClass(cls):
        super(AboutViewTest, cls).setUpClass()
        site = Site(domain='testserver', name='test')
        site.save()
        theme = SiteTheme(site=site, theme_dir_name='philu')
        theme.save()

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch.object(DiscoveryClient, '__init__', Mock(return_value=None))
    @patch.object(DiscoveryClient, 'get_program', Mock(return_value=mock_get_program()))
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_program_has_no_courses(self, mock_webpack_loader):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 0)

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch.object(DiscoveryClient, '__init__', Mock(return_value=None))
    @patch.object(DiscoveryClient, 'get_program', Mock(return_value=mock_get_program([mock_course()])))
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_courses_without_runs(self, mock_webpack_loader):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 0)

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch.object(DiscoveryClient, '__init__', Mock(return_value=None))
    @patch.object(DiscoveryClient, 'get_program', Mock(return_value=mock_get_program_with_runs_having_no_dates()))
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_courses_with_runs_having_no_dates(self, mock_webpack_loader):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 1)

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch.object(DiscoveryClient, '__init__', Mock(return_value=None))
    @patch.object(DiscoveryClient, 'get_program', Mock(return_value=mock_get_program_with_open_course_runs()))
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_courses_with_open_runs(self, mock_webpack_loader):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 1)
        self.assertTrue(response.mako_context['courses'][0]['opened'])

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch.object(DiscoveryClient, '__init__', Mock(return_value=None))
    @patch.object(DiscoveryClient, 'get_program', Mock(return_value=mock_get_program_with_closed_course_runs()))
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_courses_with_closed_runs(self, mock_webpack_loader):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 1)
        self.assertFalse(response.mako_context['courses'][0]['opened'])

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch.object(DiscoveryClient, '__init__', Mock(return_value=None))
    @patch.object(DiscoveryClient, 'get_program', Mock(return_value=mock_get_program_with_future_course_runs()))
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_courses_with_future_runs(self, mock_webpack_loader):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 1)
        self.assertFalse(response.mako_context['courses'][0]['opened'])

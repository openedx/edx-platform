from mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from openedx.core.djangolib.testing.philu_utils import (
    intercept_renderer, configure_philu_theme
)

from mock_get_program_helpers import (
    mock_get_program, mock_course,
    mock_get_program_with_runs_having_no_dates,
    mock_get_program_with_open_course_runs,
    mock_get_program_with_closed_course_runs,
    mock_get_program_with_future_course_runs,
)


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
        configure_philu_theme()

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch('openedx.features.specializations.views.DiscoveryClient')
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_program_has_no_courses(self, mock_webpack_loader, mock_discovery_client):
        """Mock get_program to return programs having no courses"""
        mock_discovery_client().get_program.return_value = mock_get_program()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 0)

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch('openedx.features.specializations.views.DiscoveryClient')
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_courses_without_runs(self, mock_webpack_loader, mock_discovery_client):
        """Mock get_program to return programs having courses which don't include any run"""
        mock_discovery_client().get_program.return_value = mock_get_program([mock_course()])
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 0)

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch('openedx.features.specializations.views.DiscoveryClient')
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_courses_with_runs_having_no_dates(self, mock_webpack_loader, mock_discovery_client):
        mock_discovery_client().get_program.return_value = mock_get_program_with_runs_having_no_dates()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 1)

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch('openedx.features.specializations.views.DiscoveryClient')
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_courses_with_open_runs(self, mock_webpack_loader, mock_discovery_client):
        mock_discovery_client().get_program.return_value = mock_get_program_with_open_course_runs()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 1)
        self.assertTrue(response.mako_context['courses'][0]['opened'])

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch('openedx.features.specializations.views.DiscoveryClient')
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_courses_with_closed_runs(self, mock_webpack_loader, mock_discovery_client):
        mock_discovery_client().get_program.return_value = mock_get_program_with_closed_course_runs()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 1)
        self.assertFalse(response.mako_context['courses'][0]['opened'])

    @patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    @patch('openedx.features.specializations.views.DiscoveryClient')
    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_courses_with_future_runs(self, mock_webpack_loader, mock_discovery_client):
        mock_discovery_client().get_program.return_value = mock_get_program_with_future_course_runs()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.mako_context['courses']), 1)
        self.assertFalse(response.mako_context['courses'][0]['opened'])

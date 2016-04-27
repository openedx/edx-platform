"""
Tests for the Programs.
"""

from mock import patch
from provider.oauth2.models import Client
from provider.constants import CONFIDENTIAL
from unittest import skipUnless

from django.conf import settings
from django.test import TestCase

from openedx.core.djangoapps.programs.views import get_course_programs_for_dashboard
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from student.tests.factories import UserFactory


@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestGetXSeriesPrograms(ProgramsApiConfigMixin, TestCase):
    """
    Tests for the Programs views.
    """

    def setUp(self, **kwargs):  # pylint: disable=unused-argument
        super(TestGetXSeriesPrograms, self).setUp()
        self.create_config(enabled=True, enable_student_dashboard=True)
        Client.objects.get_or_create(name="programs", client_type=CONFIDENTIAL)
        self.user = UserFactory()
        self.programs_api_response = {
            "results": [
                {
                    'category': 'xseries',
                    'status': 'active',
                    'subtitle': 'Dummy program 1 for testing',
                    'name': 'First Program',
                    'organization': {'display_name': 'Test Organization 1', 'key': 'edX'},
                    'course_codes': [
                        {
                            'organization': {'display_name': 'Test Organization 1', 'key': 'edX'},
                            'display_name': 'Demo XSeries Program 1',
                            'key': 'TEST_A',
                            'run_modes': [
                                {'sku': '', 'mode_slug': 'ABC_1', 'course_key': 'edX/DemoX_1/Run_1'},
                                {'sku': '', 'mode_slug': 'ABC_2', 'course_key': 'edX/DemoX_2/Run_2'},
                            ]
                        }
                    ],
                    'marketing_slug': 'fake-marketing-slug-xseries-1',
                },
                {
                    'category': 'xseries',
                    'status': 'active',
                    'subtitle': 'Dummy program 2 for testing',
                    'name': 'Second Program',
                    'organization': {'display_name': 'Test Organization 2', 'key': 'edX'},
                    'course_codes': [
                        {
                            'organization': {'display_name': 'Test Organization 2', 'key': 'edX'},
                            'display_name': 'Demo XSeries Program 2',
                            'key': 'TEST_B',
                            'run_modes': [
                                {'sku': '', 'mode_slug': 'XYZ_1', 'course_key': 'edX/Program/Program_Run'},
                            ]
                        }
                    ],
                    'marketing_slug': 'fake-marketing-slug-xseries-2',
                }
            ]
        }

    def test_get_course_programs_with_valid_user_and_courses(self):
        """ Test that the method 'get_course_programs_for_dashboard' returns
        only matching courses from the xseries programs in the expected format.
        """
        # mock the request call
        with patch('slumber.Resource.get') as mock_get:
            mock_get.return_value = self.programs_api_response

            # first test with user having multiple courses in a single xseries
            programs = get_course_programs_for_dashboard(
                self.user,
                ['edX/DemoX_1/Run_1', 'edX/DemoX_2/Run_2', 'valid/edX/Course']
            )
            expected_output = {
                'edX/DemoX_1/Run_1': {
                    'category': 'xseries',
                    'status': 'active',
                    'subtitle': 'Dummy program 1 for testing',
                    'name': 'First Program',
                    'course_codes': [
                        {
                            'organization': {'display_name': 'Test Organization 1', 'key': 'edX'},
                            'display_name': 'Demo XSeries Program 1',
                            'key': 'TEST_A',
                            'run_modes': [
                                {'sku': '', 'mode_slug': 'ABC_1', 'course_key': 'edX/DemoX_1/Run_1'},
                                {'sku': '', 'mode_slug': 'ABC_2', 'course_key': 'edX/DemoX_2/Run_2'},
                            ]
                        }
                    ],
                    'organization': {'display_name': 'Test Organization 1', 'key': 'edX'},
                    'marketing_slug': 'fake-marketing-slug-xseries-1',
                },
                'edX/DemoX_2/Run_2': {
                    'category': 'xseries',
                    'status': 'active',
                    'subtitle': 'Dummy program 1 for testing',
                    'name': 'First Program',
                    'course_codes': [
                        {
                            'organization': {'display_name': 'Test Organization 1', 'key': 'edX'},
                            'display_name': 'Demo XSeries Program 1',
                            'key': 'TEST_A',
                            'run_modes': [
                                {'sku': '', 'mode_slug': 'ABC_1', 'course_key': 'edX/DemoX_1/Run_1'},
                                {'sku': '', 'mode_slug': 'ABC_2', 'course_key': 'edX/DemoX_2/Run_2'},
                            ]
                        }
                    ],
                    'organization': {'display_name': 'Test Organization 1', 'key': 'edX'},
                    'marketing_slug': 'fake-marketing-slug-xseries-1',
                },
            }
            self.assertTrue(mock_get.called)
            self.assertEqual(expected_output, programs)
            self.assertEqual(sorted(programs.keys()), ['edX/DemoX_1/Run_1', 'edX/DemoX_2/Run_2'])

            # now test with user having multiple courses across two different
            # xseries
            mock_get.reset_mock()
            programs = get_course_programs_for_dashboard(
                self.user,
                ['edX/DemoX_1/Run_1', 'edX/DemoX_2/Run_2', 'edX/Program/Program_Run', 'valid/edX/Course']
            )
            expected_output['edX/Program/Program_Run'] = {
                'category': 'xseries',
                'status': 'active',
                'subtitle': 'Dummy program 2 for testing',
                'name': 'Second Program',
                'course_codes': [
                    {
                        'organization': {'display_name': 'Test Organization 2', 'key': 'edX'},
                        'display_name': 'Demo XSeries Program 2',
                        'key': 'TEST_B',
                        'run_modes': [
                            {'sku': '', 'mode_slug': 'XYZ_1', 'course_key': 'edX/Program/Program_Run'},
                        ]
                    }
                ],
                'organization': {'display_name': 'Test Organization 2', 'key': 'edX'},
                'marketing_slug': 'fake-marketing-slug-xseries-2',
            }
            self.assertTrue(mock_get.called)
            self.assertEqual(expected_output, programs)
            self.assertEqual(
                sorted(programs.keys()),
                ['edX/DemoX_1/Run_1', 'edX/DemoX_2/Run_2', 'edX/Program/Program_Run']
            )

    def test_get_course_programs_with_api_client_exception(self):
        """ Test that the method 'get_course_programs_for_dashboard' returns
        empty dictionary in case of an exception coming from patching slumber
        based client 'programs_api_client'.
        """
        # mock the request call
        with patch('edx_rest_api_client.client.EdxRestApiClient.__init__') as mock_init:
            # test output in case of any exception
            mock_init.side_effect = Exception('exc')
            programs = get_course_programs_for_dashboard(
                self.user,
                ['edX/DemoX_1/Run_1', 'valid/edX/Course']
            )
            self.assertTrue(mock_init.called)
            self.assertEqual(programs, {})

    def test_get_course_programs_with_exception(self):
        """ Test that the method 'get_course_programs_for_dashboard' returns
        empty dictionary in case of exception while accessing programs service.
        """
        # mock the request call
        with patch('slumber.Resource.get') as mock_get:
            # test output in case of any exception
            mock_get.side_effect = Exception('exc')
            programs = get_course_programs_for_dashboard(
                self.user,
                ['edX/DemoX_1/Run_1', 'valid/edX/Course']
            )
            self.assertTrue(mock_get.called)
            self.assertEqual(programs, {})

    def test_get_course_programs_with_non_existing_courses(self):
        """ Test that the method 'get_course_programs_for_dashboard' returns
        only those program courses which exists in the programs api response.
        """
        # mock the request call
        with patch('slumber.Resource.get') as mock_get:
            mock_get.return_value = self.programs_api_response
            self.assertEqual(
                get_course_programs_for_dashboard(self.user, ['invalid/edX/Course']), {}
            )
            self.assertTrue(mock_get.called)

    def test_get_course_programs_with_empty_response(self):
        """ Test that the method 'get_course_programs_for_dashboard' returns
        empty dict if programs rest api client returns empty response.
        """
        # mock the request call
        with patch('slumber.Resource.get') as mock_get:
            mock_get.return_value = {}
            self.assertEqual(
                get_course_programs_for_dashboard(self.user, ['edX/DemoX/Run']), {}
            )
            self.assertTrue(mock_get.called)

    @patch('openedx.core.djangoapps.programs.views.log.exception')
    def test_get_course_programs_with_invalid_response(self, log_exception):
        """ Test that the method 'get_course_programs_for_dashboard' logs
        the exception message if rest api client returns invalid data.
        """
        program = {
            'category': 'xseries',
            'status': 'active',
            'subtitle': 'Dummy program 1 for testing',
            'name': 'First Program',
            'organization': {'display_name': 'Test Organization 1', 'key': 'edX'},
            'course_codes': [
                {
                    'organization': {'display_name': 'Test Organization 1', 'key': 'edX'},
                    'display_name': 'Demo XSeries Program 1',
                    'key': 'TEST_A',
                    'run_modes': [
                        {'sku': '', 'mode_slug': 'ABC_2'},
                    ]
                }
            ],
            'marketing_slug': 'fake-marketing-slug-xseries-1',
        }
        invalid_programs_api_response = {"results": [program]}
        # mock the request call
        with patch('slumber.Resource.get') as mock_get:
            mock_get.return_value = invalid_programs_api_response
            programs = get_course_programs_for_dashboard(self.user, ['edX/DemoX/Run'])
            log_exception.assert_called_with(
                'Unable to parse Programs API response: %r',
                program
            )
            self.assertEqual(programs, {})

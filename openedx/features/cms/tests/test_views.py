"""
Unit tests for CMS application views
"""
from datetime import datetime

import mock
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test.client import Client
from opaque_keys.edx.locator import CourseLocator
from pytz import UTC

from cms.djangoapps.contentstore.views.course import get_in_process_course_actions
from openedx.core.djangolib.testing.philu_utils import configure_philu_theme
from openedx.features.cms import views as rerun_views
from xmodule.course_module import CourseFields
from xmodule.modulestore.exceptions import DuplicateCourseError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from . import helpers as test_helpers
from ..constants import ERROR_MESSAGES


class CourseRerunAutomationViewTestCase(ModuleStoreTestCase):
    """
    Class for test cases related to course re-run, automation, views
    """

    def setUp(self):
        super(CourseRerunAutomationViewTestCase, self).setUp()
        self.factory = RequestFactory()
        # creating groups of courses (and reruns), to get latest courses
        self.latest_course = test_helpers.create_course(self.store, self.user)
        self.rerun_path = reverse('course_multiple_rerun')

    @classmethod
    def setUpClass(cls):
        super(CourseRerunAutomationViewTestCase, cls).setUpClass()
        configure_philu_theme()

    def test_course_multiple_rerun_handler_denies_anonymous(self):
        """This method test API call without logged-in user. In this case user must be redirected
         to login page
        """
        response = Client().get(path=self.rerun_path)
        self.assertRedirects(
            response,
            '{sign_in}?next={next_url}'.format(sign_in=reverse('signin_user'), next_url=self.rerun_path)
        )

    @mock.patch('openedx.features.cms.views.render_to_response')
    @mock.patch('openedx.features.cms.views.helpers.latest_course_reruns')
    @mock.patch('openedx.features.cms.views.create_multiple_reruns')
    @mock.patch('openedx.features.cms.views.get_courses_accessible_to_user')
    def test_course_multiple_rerun_handler_listing(
        self, mock_get_courses_accessible_to_user, mock_create_multiple_reruns,
            mock_latest_course_reruns, mock_render_to_response):
        """
        Testing get call to API, for latest course listing, to create rerun from
        """

        request = self.factory.get(self.rerun_path)
        request.user = self.user

        # Get all course summaries from the store
        courses = self.store.get_course_summaries()

        mock_get_courses_accessible_to_user.return_value = (courses, list())
        mock_latest_course_reruns.return_value = self.latest_course

        rerun_views.course_multiple_rerun_handler(request)

        assert not mock_create_multiple_reruns.called
        mock_get_courses_accessible_to_user.assert_called_once_with(request)
        mock_latest_course_reruns.assert_called_once_with(courses)

        expected_context = {
            'latest_courses': self.latest_course
        }

        mock_render_to_response.assert_called_once_with('rerun/create_multiple_rerun.html',
                                                        expected_context)

    @mock.patch('openedx.features.cms.views.render_to_response')
    @mock.patch('openedx.features.cms.views.helpers.latest_course_reruns')
    @mock.patch('openedx.features.cms.views.create_multiple_reruns')
    @mock.patch('openedx.features.cms.views.get_courses_accessible_to_user')
    def test_course_multiple_rerun_handler_create_rerun(
        self, mock_get_courses_accessible_to_user, mock_create_multiple_reruns,
            mock_latest_course_reruns, mock_render_to_response):
        """
        Testing post call to API, for creating rerun from json data
        """

        request = self.factory.post(self.rerun_path, data='{"dummy":"data"}',
                                    content_type='application/json')
        request.user = self.user

        # Get all course summaries from the store
        courses = self.store.get_course_summaries()

        in_process_course_actions = get_in_process_course_actions(request)
        mock_get_courses_accessible_to_user.return_value = (courses, in_process_course_actions)
        mock_latest_course_reruns.return_value = self.latest_course

        # calling actual function with mocked data and request
        response = rerun_views.course_multiple_rerun_handler(request)

        self.assertEqual(response.status_code, 200)
        mock_get_courses_accessible_to_user.assert_called_once_with(request)

        course_ids = [str(course.id) for course in courses]
        mock_create_multiple_reruns.assert_called_once_with(mock.ANY, course_ids, request.user)

        assert not mock_latest_course_reruns.called
        assert not mock_render_to_response.called

    @mock.patch('openedx.features.cms.views.render_to_response')
    @mock.patch('openedx.features.cms.views.helpers.latest_course_reruns')
    @mock.patch('openedx.features.cms.views.create_multiple_reruns')
    @mock.patch('openedx.features.cms.views.get_courses_accessible_to_user')
    def test_course_multiple_rerun_handler_raise_rerun_exception(
        self, mock_get_courses_accessible_to_user, mock_create_multiple_reruns,
            mock_latest_course_reruns, mock_render_to_response):
        request = self.factory.post(self.rerun_path, data='{"dummy":"data"}',
                                    content_type='application/json')
        request.user = self.user

        # using empty course summary list in mock to raise error
        mock_get_courses_accessible_to_user.return_value = (list(), list())
        mock_create_multiple_reruns.side_effect = Exception()

        # calling actual function with mocked data and request
        response = rerun_views.course_multiple_rerun_handler(request)

        self.assertEqual(response.status_code, 400)
        mock_get_courses_accessible_to_user.assert_called_once_with(request)

        mock_create_multiple_reruns.assert_called_once()

        assert not mock_latest_course_reruns.called
        assert not mock_render_to_response.called

    @mock.patch('openedx.features.cms.views._rerun_course')
    @mock.patch('openedx.features.cms.views.helpers.update_course_re_run_details')
    def test_create_multiple_reruns(self, mock_update_course_re_run_details, mock_rerun_course):
        # Input dictionary for the method (as param), which we are testing
        course_rerun_details = [
            {
                "runs": [
                    {"release_number": "1.33", "start_date": "10/01/2019", "start_time": "00:00"}
                ],
                "source_course_key": "organization/Phy101/1_1.33_20091001_20100101"
            },
            {
                "runs": [
                    {"release_number": "1.33", "start_date": "10/01/2019", "start_time": "00:00"},
                    {"release_number": "1.34", "start_date": "10/01/2018", "start_time": "00:00"}
                ],
                "source_course_key": "course-v1:organization+CS101+4_1.31_20091001_20100101"
            }
        ]

        # expected course rerun details is an intermediate data format. It will eventually transform
        # to expected return value
        expected_course_re_run_details = [
            {
                'source_course_key': CourseLocator('organization', 'Phy101',
                                                   '1_1.33_20091001_20100101',
                                                   deprecated=True),
                'runs': [
                    {
                        'start': datetime(2019, 10, 1, tzinfo=UTC),
                        'start_time': '00:00', 'run': '2_1.33_20191001_20200101',
                        'start_date': '10/01/2019', 'release_number': '1.33'
                    }
                ],
                'org': 'organization', 'display_name': 'Physics', 'number': 'Phy101'
            },
            {
                'source_course_key': CourseLocator('organization', 'CS101',
                                                   '4_1.31_20091001_20100101'),
                'runs': [
                    {
                        'start': datetime(2019, 10, 1, tzinfo=UTC), 'start_time': '00:00',
                        'run': '5_1.33_20191001_20200101', 'start_date': '10/01/2019',
                        'release_number': '1.33'
                    },
                    {
                        'start': datetime(2018, 10, 1, tzinfo=UTC), 'start_time': '00:00',
                        'run': '6_1.34_20181001_20190101', 'start_date': '10/01/2018',
                        'release_number': '1.34'
                    }
                ],
                'org': 'organization', 'display_name': 'Computer Science', 'number': 'CS101'
            }
        ]

        mock_update_course_re_run_details.return_value = expected_course_re_run_details

        # get course ids from all course summaries in store
        course_ids = [course.id.html_id() for course in self.store.get_course_summaries()]

        # calling actual function with mocked data and request
        rerun_views.create_multiple_reruns(course_rerun_details, course_ids, self.user)

        mock_update_course_re_run_details.assert_called_once_with(course_rerun_details)

        # The expected output of the method, which we are testing
        expected_re_runs = [
            {
                'source_course_key': CourseLocator('organization', 'Phy101',
                                                   '1_1.33_20091001_20100101', deprecated=True),
                'fields': {
                    'start': datetime(2019, 10, 1, tzinfo=UTC),
                    'advertised_start': None, 'display_name': 'Physics',
                    'wiki_slug': 'organization.Phy101.2_1.33_20191001_20200101'
                },
                'destination_course_key': CourseLocator('organization', 'Phy101',
                                                        '2_1.33_20191001_20200101'),
                'user': self.user
            },
            {
                'source_course_key': CourseLocator('organization', 'CS101',
                                                   '4_1.31_20091001_20100101'),
                'fields': {
                    'start': datetime(2019, 10, 1, tzinfo=UTC),
                    'advertised_start': None,
                    'display_name': 'Computer Science',
                    'wiki_slug': 'organization.CS101.5_1.33_20191001_20200101'
                },
                'destination_course_key': CourseLocator('organization', 'CS101',
                                                        '5_1.33_20191001_20200101'),
                'user': self.user
            },
            {
                'source_course_key': CourseLocator('organization', 'CS101',
                                                   '4_1.31_20091001_20100101'),
                'fields': {
                    'start': datetime(2018, 10, 1, tzinfo=UTC),
                    'advertised_start': None, 'display_name': 'Computer Science',
                    'wiki_slug': 'organization.CS101.6_1.34_20181001_20190101'
                },
                'destination_course_key': CourseLocator('organization', 'CS101',
                                                        '6_1.34_20181001_20190101'),
                'user': self.user
            }
        ]

        all_rerun_mock_calls = [mock.call(**re_run_arguments) for re_run_arguments in
                                expected_re_runs]

        mock_rerun_course.assert_has_calls(all_rerun_mock_calls)

    def test_create_multiple_reruns_invalid_start_date(self):
        course_re_run_details = [
            {
                "runs": [
                    {
                        "release_number": "1.33", "start_date": "100/12/2019", "start_time": "00:00"
                    }
                ],
                "source_course_key": "course-v1:organization+CS101+4_1.31_20091001_20100101"
            }
        ]

        with self.assertRaises(ValueError) as error:
            rerun_views.create_multiple_reruns(course_re_run_details, mock.ANY, self.user)

        expected_error_message = ERROR_MESSAGES['start_date_format_mismatch']
        runs_0_data = course_re_run_details[0]['runs'][0]

        self.assertEqual(expected_error_message, str(error.exception))
        self.assertEqual(expected_error_message, runs_0_data['error'])

    def test_create_multiple_reruns_from_unknown_course(self):
        # Input dictionary for the method (as param), which we are testing
        course_re_run_details = [
            {
                "runs": [
                    {
                        "release_number": "1.33", "start_date": "10/01/2019", "start_time": "00:00"
                    }
                ],
                "source_course_key": "course-v1:unknown+unknown+unknown"
            }
        ]

        # get course ids from all course summaries in store
        course_ids = [course.id.html_id() for course in self.store.get_course_summaries()]
        with self.assertRaises(ValueError) as error:
            rerun_views.create_multiple_reruns(course_re_run_details, course_ids, self.user)

        expected_error_message = ERROR_MESSAGES['course_key_not_found']

        self.assertEqual(expected_error_message, str(error.exception))
        self.assertEqual(expected_error_message, course_re_run_details[0]['error'])

    @mock.patch('openedx.features.cms.views.helpers.update_course_re_run_details')
    def test_create_multiple_reruns_user_has_no_access_to_course(
            self, mock_update_course_re_run_details):
        # Input dictionary for the method (as param), which we are testing
        course_re_run_details = [
            {
                "runs": [
                    {
                        "release_number": "1.33", "start_date": "10/01/2019", "start_time": "00:00"
                    }
                ],
                "source_course_key": "course-v1:organization+CS101+4_1.31_20091001_20100101"
            }
        ]

        # The expected intermediate output data format
        expected_course_re_run_details = [
            {
                'source_course_key': CourseLocator('organization', 'CS101',
                                                   '4_1.31_20091001_20100101'),
                'org': 'organization',
                'runs': [
                    {
                        'start': datetime(2019, 10, 1, tzinfo=UTC),
                        'start_time': '00:00', 'run': '5_1.33_20191001_20200101',
                        'start_date': '10/01/2019', 'release_number': '1.33'
                    }
                ],
                'display_name': 'Computer Science', 'number': 'CS101'
            }
        ]

        mock_update_course_re_run_details.return_value = expected_course_re_run_details
        # get course ids from all course summaries in store
        course_ids = [course.id.html_id() for course in self.store.get_course_summaries()]
        with self.assertRaises(PermissionDenied) as error:
            rerun_views.create_multiple_reruns(course_re_run_details, course_ids, AnonymousUser())

        expected_error_message = ERROR_MESSAGES['unauthorized_user']

        self.assertEqual(expected_error_message, str(error.exception))
        self.assertEqual(expected_error_message, expected_course_re_run_details[0]['error'])

    @mock.patch('openedx.features.cms.views.helpers.update_course_re_run_details')
    def test_create_multiple_reruns_raise_duplicate_course_error(
            self, mock_update_course_re_run_details):
        # Input dictionary for the method (as param), which we are testing
        course_re_run_details = [
            {
                "runs": [
                    {
                        "release_number": "1.33", "start_date": "10/01/2019", "start_time": "00:00"
                    }
                ],
                "source_course_key": "course-v1:organization+CS101+4_1.31_20091001_20100101"
            }
        ]

        # The expected intermediate output data format
        expected_course_re_run_details = [
            {
                'source_course_key': CourseLocator('organization', 'CS101',
                                                   '4_1.31_20091001_20100101'),
                'org': 'organization',
                'runs': [
                    {
                        'start': datetime(2019, 10, 1, tzinfo=UTC),
                        'start_time': '00:00', 'run': '4_1.31_20091001_20100101',
                        'start_date': '10/01/2019', 'release_number': '1.33'
                    }
                ],
                'display_name': 'Computer Science', 'number': 'CS101'
            }
        ]

        mock_update_course_re_run_details.return_value = expected_course_re_run_details
        # get course ids from all course summaries in store
        course_ids = [course.id.html_id() for course in self.store.get_course_summaries()]
        with self.assertRaises(DuplicateCourseError) as error:
            rerun_views.create_multiple_reruns(course_re_run_details, course_ids, self.user)

        expected_error_message = ERROR_MESSAGES['duplicate_course_id']
        runs_0_data = expected_course_re_run_details[0]['runs'][0]

        self.assertIn('duplicates', str(error.exception))
        self.assertEqual(expected_error_message, runs_0_data['error'])

    @mock.patch('openedx.features.cms.views.add_instructor')
    def test_rerun_course(self, mock_add_instructor):
        source_course = CourseFactory.create(
            display_name='parent_course',
            org='organization',
            number='parent',
            run='dummy_source_course_key',
            modulestore=self.store,
            emit_signals=True
        )

        fields = dict()
        fields['start'] = CourseFields.start.default
        fields['display_name'] = "Unit test rerun"

        destination_course_key = CourseLocator(
            org='TesOrg', course='Test101', run='TestKey_1.1_100'
        )

        # pylint: disable=protected-access
        rerun_views._rerun_course(source_course.id, destination_course_key, self.user, fields)

        # Get all course summaries from the store
        courses = self.store.get_course_summaries()

        # find the rerun we created, from course summaries
        destination_course_rerun = next(
            (course for course in courses if course.id == destination_course_key), None)

        assert mock_add_instructor.called
        self.assertEqual(destination_course_rerun.id, destination_course_key)
        self.assertEqual(destination_course_rerun.display_name, fields['display_name'])

    def tearDown(self):
        self.client.logout()
        super(CourseRerunAutomationViewTestCase, self).tearDown()
